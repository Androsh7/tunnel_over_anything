"""Defines the packet_assembler class for converting outbound packets to the transport packets"""

# Standard libraries
import os
from base64 import b64decode, b64encode, b85decode, b85encode
from typing import Optional
from urllib import parse

# Third-party libraries
from attrs import define, field, validators
from loguru import logger

# Project libraries
import src.default as df
from src.load_config import PacketConfig
from src.packet_lib.dns import assemble_dns_packet, disassemble_dns_packet
from src.packet_queue import PacketQueue


@define
class PacketConverter:
    """Defines the PacketConverter class for turning raw data into DNS packets or
    disassembling DNS packets to extract the raw binary data"""

    packet_type: str = field(
        validator=validators.and_(
            validators.instance_of(str), validators.in_(df.PROTOCOLS)
        )
    )
    encoding: str = field(
        validator=validators.and_(
            validators.instance_of(str), validators.in_(df.ENCODING_TYPES)
        )
    )
    mode: str = field(
        validator=validators.and_(
            validators.instance_of(str), validators.in_(("client", "server"))
        )
    )
    assemble_source_queue: PacketQueue = field(
        validator=validators.instance_of(PacketQueue)
    )
    assemble_destination_queue: PacketQueue = field(
        validator=validators.instance_of(PacketQueue)
    )
    disassemble_source_queue: PacketQueue = field(
        validator=validators.instance_of(PacketQueue)
    )
    disassemble_destination_queue: PacketQueue = field(
        validator=validators.instance_of(PacketQueue)
    )

    def __init__(
        self,
        config: PacketConfig,
        from_server: PacketQueue,
        to_server: PacketQueue,
        from_client: PacketQueue,
        to_client: PacketQueue,
    ):
        self.packet_type = config.protocol
        self.encoding = config.encoding
        self.mode = config.mode

        if self.mode == "client":
            self.assemble_source_queue = from_server
            self.assemble_destination_queue = to_client
            self.disassemble_source_queue = from_client
            self.disassemble_destination_queue = to_server
        elif self.mode == "server":
            self.assemble_source_queue = from_client
            self.assemble_destination_queue = to_server
            self.disassemble_source_queue = from_server
            self.disassemble_destination_queue = to_client
        else:
            raise KeyError(f"Invalid mode {self.mode} for PacketConverter")

    def encode_data(self, data: bytes) -> bytes:
        """Encodes data to the protocol specified in the PacketConverter config

        Args:
            data: byte string to encode

        Returns:
            encoded byte string
        """
        match (self.encoding):
            case "base64":
                return b64encode(data)
            case "base85":
                return bytes(parse.quote_from_bytes(b85encode(data)), encoding="ascii")
            case "none":
                return data
            case _:
                raise KeyError(
                    f"Invalid or unsupported encoding method {self.encoding}"
                )

    def decode_data(self, data: bytes) -> bytes:
        """Decodes data to the protocol specified in the PacketConverter config

        Args:
            data: byte string to decode

        Returns:
            Decoded byte string
        """
        match (self.encoding):
            case "base64":
                return b64decode(data)
            case "base85":
                return b85decode(parse.unquote_to_bytes(data))
            case "none":
                return data
            case _:
                raise KeyError(
                    f"Invalid or unsupported encoding method {self.encoding}"
                )

    def assemble_packet(self, data: bytes) -> bytes:
        """Takes a byte string and assembles it into a DNS packet

        Args:
            data: The data to hide in the DNS packet

        Raises:
            KeyError: Raises an error if the PacketConverter object
                has an invalid or unsupported packet_type

        Returns:
            The assembled packet as a byte string
        """
        encoded_data = self.encode_data(data)
        match self.packet_type:
            case "dns":
                return assemble_dns_packet(encoded_data)
            case "none":
                return encoded_data
            case _:
                raise KeyError(f"[assembler] Invalid packet type {self.packet_type}")

    def disassemble_packet(self, packet: bytes) -> Optional[bytes]:
        """Takes an assembled packet and returns the hidden data

        Args:
            data: The packet bytes to dissect

        Raises:
            KeyError: Raises an error if the PacketConverter object
                has an invalid or unsupported packet_type

        Returns:
            The data hidden in the packet as a byte string or None
                if the dissection failed
        """
        encoded_data = None
        match self.packet_type:
            case "dns":
                encoded_data = disassemble_dns_packet(packet_bytes=packet)
            case "none":
                encoded_data = packet
            case _:
                raise KeyError(f"[disassembler] Invalid packet type {self.packet_type}")
        if encoded_data is None:
            return encoded_data

        return self.decode_data(encoded_data)

    def assembler_service(self):
        """Starts the assemble packets service, this takes packets from raw_capture and
        builds them into assembled DNS packets in assembled_packets
        """
        logger.info(
            f"[assembler] Started packet assembler "
            f"({self.assemble_source_queue} -> {self.assemble_destination_queue})"
        )
        while True:
            # skip if the queue is empty
            if self.assemble_source_queue.is_empty():
                continue
            packet_bytes = self.assemble_source_queue.dequeue()
            assembled_packet = self.assemble_packet(data=packet_bytes)
            self.assemble_destination_queue.enqueue(assembled_packet)

    def disassembler_service(self):
        """Starts the packet disassembly service, this takes assembled DNS packets from
        inbound/raw_capture and dissects the data into inbound/disassembled_packets
        """
        logger.info(
            f"[disassembler] Started packet disassembler "
            f"({self.disassemble_source_queue} -> {self.disassemble_destination_queue})"
        )
        while True:
            # skip if the queue is empty
            if self.disassemble_source_queue.is_empty():
                continue

            packet_bytes = self.disassemble_source_queue.dequeue()
            if packet_bytes is None:
                continue
            if (
                disassembled_packet := self.disassemble_packet(packet=packet_bytes)
            ) is None:
                continue

            self.disassemble_destination_queue.enqueue(disassembled_packet)
