# Defines the packet_assembler class for converting outbound packets to the transport packets

# Standard libraries
import os
from base64 import b64encode, b64decode
from typing import Literal

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
                raise KeyError(f"Invalid packet type {self.packet_type}")

    def disassemble_dns(self, data: bytes) -> bytes:
        match self.packet_type:
            case "dns":
                encoded_data = disassemble_dns_packet(packet_bytes=data)
            case _:
                raise KeyError(f"Invalid packet type {self.packet_type}")
        
        return b64decode(encoded_data)

    def assemble_packets(self):
        logger.debug(
            f"[+] Started packet assembler (outbound/raw_capture -> outbound/assembled_packets)"
        )
        while True:
            packet_list = self.grab_captures(dir="outbound")
            if len(packet_list) == 0:
                continue
            logger.debug(
                f'[+] Processing {len(packet_list)} packet{"s" if len(packet_list) > 1 else ""} in outbound/raw_capture'
            )

            for packet in packet_list:
                packet_path = f"{df.CLIENT_DIR}/outbound/raw_capture/{packet}"
                packet_bytes = self.read_packet(path=packet_path)
                logger.trace(
                    f"[+] Assembling {len(packet_bytes)} bytes to packet outbound/assembled_packets/{packet}"
                )

                assembled_packet = self.assemble_dns(data=packet_bytes)

                self.write_packet(
                    path=f"{df.CLIENT_DIR}/outbound/assembled_packets/{packet}",
                    packet=assembled_packet,
                )
                self.delete_packet(packet_path)

    def disassemble_packets(self):
        logger.debug(
            f"[+] Started packet disassembler (inbound/raw_capture -> inbound/disassembled_packets)"
        )
        while True:
            packet_list = self.grab_captures(dir="inbound")
            if len(packet_list) == 0:
                continue
            logger.debug(
                f'[+] Processing {len(packet_list)} packet{"s" if len(packet_list) > 1 else ""} in inbound/raw_capture'
            )

            for packet in packet_list:
                packet_path = f"{df.CLIENT_DIR}/inbound/raw_capture/{packet}"
                packet_bytes = self.read_packet(path=packet_path)
                logger.trace(
                    f"[+] Disassembling {len(packet_bytes)} bytes to packet inbound/disassembled_packets/{packet}"
                )

                if (disassembled_packet := self.disassemble_dns(data=packet_bytes)) is None:
                    continue

                self.write_packet(
                    path=f"{df.CLIENT_DIR}/inbound/disassembled_packets/{packet}",
                    packet=disassembled_packet,
                )
                self.delete_packet(packet_path)
