"""Base connector class for transmitting and receiving"""

# Standard libraries
import socket
from typing import Literal, Optional

# Third-party libraries
from attrs import define, field, validators
from loguru import logger

# Project libraries
import src.default as df
from src.packet_queue import PacketQueue


@define
class BaseConnector:
    """A base class for the client and server connector"""

    connector_type: Literal[(df.CONNECTOR_TYPES)] = field(
        validator=validators.and_(
            validators.instance_of(str), validators.in_(df.CONNECTOR_TYPES)
        )
    )
    endpoint: str = field(validator=validators.instance_of(str))
    port: int = field(
        validator=validators.and_(
            validators.instance_of(int), validators.ge(1), validators.le(65535)
        )
    )
    recv_path: PacketQueue = field(validator=validators.instance_of(PacketQueue))
    tx_path: PacketQueue = field(validator=validators.instance_of(PacketQueue))
    sock: socket.socket = field(validator=validators.instance_of(socket.socket))
    tx_address: tuple[str, int] = field()

    def receive(self) -> Optional[tuple[bytes, tuple[str, int]]]:
        """Listens for incoming connections and returns the message and source address

        Returns:
            The message and source address as a tuple or a (None, None) tuple if a
            connection refused message is received
        """
        try:
            data, address = self.sock.recvfrom(df.MAX_RECV_BUFFER)
        except ConnectionRefusedError:
            logger.error(f"[{self.connector_type}] Connection refused (Errno 111)")
            return (None, None)
        return data, address

    def listener_service(self):
        """Starts the listener service, this will write all incoming packets to
        the respective folder inbound/raw_capture or outbound/raw_capture
        """
        logger.info(
            f"[{self.connector_type}] Started response listener for {self.endpoint}:{self.port}"
        )
        while True:
            packet_bytes, addr = self.receive()
            # ignore if the receive command failed
            if packet_bytes is None or addr is None:
                continue

            # print the updated server transmit endpoint
            if self.tx_address != addr:
                if self.tx_address is not None:
                    logger.info(
                        f"[{self.connector_type}] transmit endpoint is changing from "
                        f"{self.tx_address[0]}:{self.tx_address[1]} to {addr[0]}:{addr[1]}"
                    )
                else:
                    logger.info(
                        f"[{self.connector_type}] initial transmit endpoint "
                        f"is set to {addr[0]}:{addr[1]}"
                    )
            self.tx_address = addr
            logger.debug(
                f"[{self.connector_type}] Received {len(packet_bytes)} byte packet from "
                f"{addr[0]}:{addr[1]} writing binary to {self.recv_path}"
            )
            self.recv_path.enqueue(packet_bytes)
