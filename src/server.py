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


@define
class ServerConnector(BaseConnector):
    """Defines the ServerConnector class to listen for ClientConnector objects
    or other client software I.E: OpenVPN client"""

    def __init__(self, config: ServerConfig):
        self.connector_type = 'server'
        self.endpoint = config.endpoint
        self.port = config.port
        self.tx_path = config.tx_path
        self.recv_path = config.recv_path
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
            f'[{self.connector_type}] Started transmitter from {self.endpoint}:{self.port}'
        )
        # wait for a tx_endpoint and tx_port to be listed
        while self.tx_address is None:
            continue
        while True:
            # grab a list of all packets and sort them oldest to newest
            packet_list = os.listdir(path=f'{df.CLIENT_DIR}/{self.tx_path}/')
            packet_list.sort()
            for packet in packet_list:
                packet_path = f'{df.CLIENT_DIR}/{self.tx_path}/{packet}'
                with open(file=packet_path, mode='rb') as file:
                    packet_bytes = file.read()

                logger.info(
                    f'[{self.connector_type}] Transmitting {len(packet_bytes)} byte packet '
                    f'{self.tx_path}/{packet} to {self.tx_address[0]}:{self.tx_address[1]}'
                )
                logger.trace(f'[{self.connector_type}] {packet_bytes}')
                self.send_to(data=packet_bytes)
                try:
                    os.remove(packet_path)
                except PermissionError:
                    logger.error(
                        f'[{self.connector_type}] Permission denied when attempting to delete {packet_path}'
                    )