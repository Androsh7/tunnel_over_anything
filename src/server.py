"""Connector class for transmitting data to the client node"""

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
from src.load_config import ServerConfig
from src.packet_queue import PacketQueue


@define
class ServerConnector(BaseConnector):
    """Defines the ServerConnector class to listen for ClientConnector objects
    or other client software I.E: OpenVPN client"""

    def __init__(
        self,
        config: ServerConfig,
        to_converter: PacketQueue,
        from_converter: PacketQueue,
    ):
        self.connector_type = "server"
        self.endpoint = config.endpoint
        self.port = config.port
        self.tx_path = from_converter
        self.recv_path = to_converter
        self.tx_address = None

        # Create the socket
        self.sock = socket.socket(
            family=socket.AddressFamily.AF_INET, type=socket.SOCK_DGRAM
        )

        # Attempt to bind to a specific port
        self.sock.bind((self.endpoint, self.port))

    def send_to(self, data: bytes) -> Optional[int]:
        """Transmits a byte string to the stored tx_address

        Args:
            data: The byte string to transmit

        Returns:
            The number of bytes transmitted or None if the
                transmission failed
        """
        try:
            return self.sock.sendto(data, self.tx_address)
        except ConnectionRefusedError as e:
            logger.error(e)
        return None

    def transmit_service(self):
        """Starts the transmit service, this will send all processed packets
        to the tx_address stored by the listener_service
        """
        logger.info(
            f"[{self.connector_type}] Started transmitter from {self.endpoint}:{self.port}"
        )
        # wait for a tx_endpoint and tx_port to be listed
        while self.tx_address is None:
            continue
        while True:
            # wait for packets to be added to the tx_path queue
            if self.tx_path.is_empty():
                continue

            packet_bytes = self.tx_path.dequeue()

            logger.debug(
                f"[{self.connector_type}] Transmitting {len(packet_bytes)} byte packet "
                f"{self.tx_path} to {self.tx_address[0]}:{self.tx_address[1]}"
            )
            self.send_to(data=packet_bytes)
