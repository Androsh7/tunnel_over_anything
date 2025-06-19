# Connector class for transmitting data to the server node

# Standard libraries
import os
import socket
from typing import Optional

# Third-party libraries
from attrs import define
from loguru import logger

# Project libraries
import src.default as df
from src.base_connector import BaseConnector
from src.load_config import ClientConfig


@define
class ClientConnector(BaseConnector):
    """Defines the ClientConnector class for connecting to a ServerConnector object
    or another server I.E: OpenVPN server"""

    def __init__(self, config: ClientConfig):
        self.connector_type = "client"
        self.endpoint = config.endpoint
        self.port = config.port
        self.tx_path = config.tx_path
        self.recv_path = config.recv_path
        self.tx_address = None

        # Create the socket
        self.sock = socket.socket(
            family=socket.AddressFamily.AF_INET, type=socket.SOCK_DGRAM
        )

        # Attempt to connect to a remote host
        self.sock.connect((self.endpoint, self.port))

    def send(self, data: bytes) -> Optional[int]:
        """Transmits a byte string to the socket endpoint and port

        Args:
            data: The byte string to transmit

        Returns:
            The number of bytes transmitted or None if the transmission failed
        """
        try:
            return self.sock.send(data)
        except ConnectionRefusedError:
            logger.error(
                f"[{self.connector_type}] Connection refused by {self.endpoint}:{self.port}"
            )
        return None

    def transmit_service(self):
        """Starts the transmit service, this will send all processed packets in
        outbound/assembled_packets or inbound/disassembled_packets to the specified
        endpoint and port
        """
        logger.info(
            f"[{self.connector_type}] Started transmitter to {self.endpoint}:{self.port}"
        )
        while True:
            # grab a list of all packets and sort them oldest to newest
            packet_list = os.listdir(path=f"{df.CLIENT_DIR}/{self.tx_path}/")
            packet_list.sort()
            for packet in packet_list:
                packet_path = f"{df.CLIENT_DIR}/{self.tx_path}/{packet}"
                with open(file=packet_path, mode="rb") as file:
                    packet_bytes = file.read()

                logger.info(
                    f"[{self.connector_type}] Transmitting {len(packet_bytes)} byte packet {self.tx_path}/{packet} to {self.endpoint}:{self.port}"
                )
                logger.trace(
                    f"[{self.connector_type}] {packet_bytes}"
                )
                self.send(data=packet_bytes)
                os.remove(packet_path)
