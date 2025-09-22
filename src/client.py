"""Connector class for transmitting data to the server node"""

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
from src.packet_queue import PacketRingBuffer


@define
class ClientConnector(BaseConnector):
    """Defines the ClientConnector class for connecting to a ServerConnector object
    or another server I.E: OpenVPN server"""

    def __init__(
        self,
        config: ClientConfig,
        to_converter: PacketRingBuffer,
        from_converter: PacketRingBuffer,
    ):
        self.connector_type = "client"
        self.endpoint = config.endpoint
        self.port = config.port
        self.tx_path = from_converter
        self.recv_path = to_converter
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
        """Starts the transmit service, this will send all
        processed packets to the specified endpoint and port
        """
        logger.info(
            f"[{self.connector_type}] Started transmitter to {self.endpoint}:{self.port}"
        )
        while True:
            # wait for packets to be added to the tx_path queue
            if self.tx_path.is_empty():
                continue

            # grab a list of all packets and sort them oldest to newest
            packet_bytes = self.tx_path.get()

            logger.debug(
                f"[{self.connector_type}] Transmitting {len(packet_bytes)} byte packet "
                f"{self.tx_path} to {self.endpoint}:{self.port}"
            )
            self.send(data=packet_bytes)
