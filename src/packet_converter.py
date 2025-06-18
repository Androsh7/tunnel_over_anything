# Defines the packet_assembler class for converting outbound packets to the transport packets

# Standard libraries
import os
from base64 import b64decode, b64encode
from typing import Literal, Optional

# Third-party libraries
from loguru import logger

# Project libraries
import src.default as df
from src.load_config import PacketConfig
from src.packet_lib.dns import assemble_dns_packet, disassemble_dns_packet


class PacketConverter:

    def __init__(self, config: PacketConfig):
        self.packet_type = config.protocol

    def grab_captures(self, dir: Literal["outbound", "inbound"]) -> list[str]:
        """Returns the list of raw packet filenames from oldest to newest

        Returns:
            List of the sorted raw packet filenames from oldest to newest
        """
        packet_list = os.listdir(path=f"{df.CLIENT_DIR}/{dir}/raw_capture")
        packet_list.sort()  # sort from oldest to newest

        return packet_list

    def read_packet(self, path: str) -> bytes:
        with open(file=path, mode="rb") as file:
            return file.read()

    def write_packet(self, path: str, packet: bytes):
        with open(file=path, mode="wb") as file:
            file.write(packet)

    def delete_packet(self, path: str):
        os.remove(path=path)

    def assemble_dns(self, data: bytes) -> bytes:
        encoded_data = b64encode(data)
        match self.packet_type:
            case "dns":
                return assemble_dns_packet(encoded_data)
            case _:
                raise KeyError(f"[assembler] Invalid packet type {self.packet_type}")

    def disassemble_dns(self, data: bytes) -> Optional[bytes]:
        match self.packet_type:
            case "dns":
                encoded_data = disassemble_dns_packet(packet_bytes=data)
            case _:
                raise KeyError(f"[disassembler] Invalid packet type {self.packet_type}")
        if encoded_data is None:
            return encoded_data

        return b64decode(encoded_data)

    def assemble_packets(self):
        logger.info(
            f"[assembler] Started packet assembler ({df.OUTBOUND_RAW_PATH} -> {df.OUTBOUND_PROCESSED_PATH})"
        )
        while True:
            packet_list = self.grab_captures(dir="outbound")
            if len(packet_list) == 0:
                continue
            logger.debug(
                f'[assembler] Processing {len(packet_list)} packet{"s" if len(packet_list) > 1 else ""} in {df.OUTBOUND_RAW_PATH} {packet_list}'
            )

            for packet in packet_list:
                packet_source_path = f"{df.OUTBOUND_RAW_PATH}/{packet}"
                packet_destination_path = f"{df.OUTBOUND_PROCESSED_PATH}/{packet}"
                packet_bytes = self.read_packet(
                    path=f"{df.CLIENT_DIR}/{packet_source_path}"
                )
                logger.debug(
                    f"[assembler] {packet_source_path} -> {packet_destination_path}"
                )

                assembled_packet = self.assemble_dns(data=packet_bytes)

                self.write_packet(
                    path=f"{df.CLIENT_DIR}/{packet_destination_path}",
                    packet=assembled_packet,
                )
                self.delete_packet(packet_source_path)

    def disassemble_packets(self):
        logger.info(
            f"[disassembler] Started packet disassembler ({df.INBOUND_RAW_PATH} -> {df.INBOUND_PROCESSED_PATH})"
        )
        while True:
            packet_list = self.grab_captures(dir="inbound")
            if len(packet_list) == 0:
                continue
            logger.debug(
                f'[disassembler] Processing {len(packet_list)} packet{"s" if len(packet_list) > 1 else ""} in {df.INBOUND_RAW_PATH} {packet_list}'
            )

            for packet in packet_list:
                packet_source_path = f"{df.INBOUND_RAW_PATH}/{packet}"
                packet_destination_path = f"{df.INBOUND_PROCESSED_PATH}/{packet}"
                packet_bytes = self.read_packet(
                    path=f"{df.CLIENT_DIR}/{packet_source_path}"
                )
                logger.debug(
                    f"[disassembler] {packet_source_path} -> {packet_destination_path}"
                )

                if (
                    disassembled_packet := self.disassemble_dns(data=packet_bytes)
                ) is None:
                    self.delete_packet(packet_source_path)
                    continue

                self.write_packet(
                    path=f"{df.CLIENT_DIR}/{packet_destination_path}",
                    packet=disassembled_packet,
                )
                self.delete_packet(packet_source_path)
