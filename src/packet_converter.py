# Defines the packet_assembler class for converting outbound packets to the transport packets

# Standard libraries
import os
from base64 import b64decode, b64encode, b85encode, b85decode
from typing import Literal, Optional
from urllib import parse

# Third-party libraries
from loguru import logger

# Project libraries
import src.default as df
from src.load_config import PacketConfig
from src.packet_lib.dns import assemble_dns_packet, disassemble_dns_packet


class PacketConverter:
    """Defines the PacketConverter class for turning raw data into DNS packets or
    disassembling DNS packets to extract the raw binary data"""

    def __init__(self, config: PacketConfig):
        self.packet_type = config.protocol
        self.encoding = config.encoding
        self.mode = config.mode

        if self.mode == 'server':
            self.assemble_source = self.assemble_source
            self.assemble_destination = self.assemble_destination
            self.disassemble_source = self.disassemble_source
            self.disassemble_destination = self.disassemble_destination
        else:
            self.disassemble_source = self.assemble_source
            self.disassemble_destination = self.assemble_destination
            self.assemble_source = self.disassemble_source
            self.assemble_destination = self.disassemble_destination

    def grab_captures(self, dir: Literal["outbound", "inbound"]) -> list[str]:
        """Returns the list of raw packet filenames from oldest to newest

        Returns:
            List of the sorted raw packet filenames from oldest to newest
        """
        packet_list = os.listdir(path=f"{df.CLIENT_DIR}/{dir}/raw_capture")
        packet_list.sort()  # sort from oldest to newest

        return packet_list

    def read_packet(self, path: str) -> bytes:
        """Returns a specified packet as a byte string

        Args:
            path: Local path to the binary file

        Returns:
            The contents of the binary files as a byte string
        """
        with open(file=path, mode="rb") as file:
            return file.read()

    def write_packet(self, path: str, packet: bytes):
        """Writes a packet byte string to a specified file

        Args:
            path: Path to the desired file
            packet: The byte string to write
        """
        with open(file=path, mode="wb") as file:
            file.write(packet)

    def delete_packet(self, path: str):
        """Deletes a given file

        Args:
            path: Path to the desired file
        """
        os.remove(path=path)

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
            decoded byte string
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
                return packet
            case _:
                raise KeyError(f"[disassembler] Invalid packet type {self.packet_type}")
        if encoded_data is None:
            return encoded_data

        return self.decode_data(encoded_data)

    def assemble_packets(self):
        """Starts the assemble packets service, this takes packets from raw_capture and
        builds them into assembled DNS packets in assembled_packets
        """
        logger.info(
            f"[assembler] Started packet assembler ({self.assemble_source} -> {self.assemble_destination})"
        )
        while True:
            packet_list = self.grab_captures(dir="outbound")
            if len(packet_list) == 0:
                continue
            logger.debug(
                f'[assembler] Processing {len(packet_list)} packet{"s" if len(packet_list) > 1 else ""} in {self.assemble_source} {packet_list}'
            )

            for packet in packet_list:
                packet_source_path = f"{self.assemble_source}/{packet}"
                packet_destination_path = f"{self.assemble_destination}/{packet}"
                packet_bytes = self.read_packet(
                    path=f"{df.CLIENT_DIR}/{packet_source_path}"
                )
                logger.debug(
                    f"[assembler] {packet_source_path} -> {packet_destination_path}"
                )

                assembled_packet = self.assemble_packet(data=packet_bytes)

                self.write_packet(
                    path=f"{df.CLIENT_DIR}/{packet_destination_path}",
                    packet=assembled_packet,
                )
                self.delete_packet(packet_source_path)

    def disassemble_packets(self):
        """Starts the packet disassembly service, this takes assembled DNS packets from
        inbound/raw_capture and dissects the data into inbound/disassembled_packets
        """
        logger.info(
            f"[disassembler] Started packet disassembler ({self.disassemble_source} -> {self.disassemble_destination})"
        )
        while True:
            packet_list = self.grab_captures(dir="inbound")
            if len(packet_list) == 0:
                continue
            logger.debug(
                f'[disassembler] Processing {len(packet_list)} packet{"s" if len(packet_list) > 1 else ""} in {self.disassemble_source} {packet_list}'
            )

            for packet in packet_list:
                packet_source_path = f"{self.disassemble_source}/{packet}"
                packet_destination_path = f"{self.disassemble_destination}/{packet}"
                packet_bytes = self.read_packet(
                    path=f"{df.CLIENT_DIR}/{packet_source_path}"
                )
                logger.debug(
                    f"[disassembler] {packet_source_path} -> {packet_destination_path}"
                )

                if (
                    disassembled_packet := self.disassemble_packet(packet=packet_bytes)
                ) is None:
                    self.delete_packet(packet_source_path)
                    continue

                self.write_packet(
                    path=f"{df.CLIENT_DIR}/{packet_destination_path}",
                    packet=disassembled_packet,
                )
                self.delete_packet(packet_source_path)
