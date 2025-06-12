# Base connector class for transmitting and receiving

# Standard libraries
import os
import socket
from typing import Optional

# Project libraries
import src.default as df

# Third-party libraries
from attrs import define, field, validators
from loguru import logger
from src.load_config import ConnectorConfig


@define
class BaseConnector:
    endpoint: str = field(validator=validators.instance_of(str))
    port: int = field(
        validator=validators.and_(
            validators.instance_of(int), validators.ge(1), validators.le(65535)
        )
    )
    recv_path: str = field(validator=validators.instance_of(str))
    tx_path: str = field(validator=validators.instance_of(str))
    sock: socket.socket = field(validator=validators.instance_of(socket.socket))
    state: str = field(
        validator=validators.and_(
            validators.in_(["bind", "connect"]), validators.instance_of(str)
        )
    )
    last_addr: tuple[str, int] = field(
        validator=validators.instance_of(tuple), default=None
    )

    def __init__(self, config: ConnectorConfig):
        self.endpoint = config.endpoint
        self.port = config.port
        self.recv_path = config.recv_path
        self.tx_path = config.tx_path
        self.state = config.connector_type
        self.last_addr = ("", 0)

        # create the socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # initiate the connection
        if config.connector_type == "bind":
            self._bind()
        elif config.connector_type == "connect":
            self._connect()
        else:
            raise KeyError(
                f'Unknown state {config.connector_type}, valid states are "bind" and "connect"'
            )

    def _connect(self):
        logger.info(f"Connecting to socket server at {self.endpoint}:{self.port}")
        self.sock.connect((self.endpoint, self.port))

    def _bind(self):
        logger.info(f"Binding socket server to {self.endpoint}:{self.port}")
        self.sock.bind((self.endpoint, self.port))

    def _get_destination(self) -> Optional[str]:
        if self.state == "bind":
            if self.last_addr[0] == '':
                return None
            return f'{self.last_addr[0]}:{self.last_addr[1]}'
        
        return f'{self.endpoint}:{self.port}'
        
    def receive(self) -> Optional[tuple[bytes, tuple[str, int]]]:
        try:
            data, address = self.sock.recvfrom(df.MAX_RECV_BUFFER)
        except ConnectionRefusedError:
            logger.error(f'Incoming connection refused {self.endpoint}:{self.port}')
            return (None, None)
        print(address)
        self.last_addr = address
        return data, address

    def send(self, data: bytes) -> Optional[int]:
        try:
            if self.state == "connect":
                return self.sock.send(data)

            return self.sock.sendto(data, self.last_addr)
        except ConnectionRefusedError:
            logger.error(f'Connection refused by {self._get_destination()}')
        return None

    def listen(self):
        logger.debug(f"[+] Started listener for {self.endpoint}:{self.port}")
        while True:
            packet_bytes, addr = self.receive()
            if packet_bytes is None:
                continue
            date_string = df.get_datetime()
            logger.trace(
                f"[+] Received {len(packet_bytes)} bytes from {addr[0]}:{addr[1]} writing packet to {self.recv_path}/{date_string}.bin"
            )
            with open(
                file=f"{df.CLIENT_DIR}/{self.recv_path}/{date_string}.bin", mode="wb"
            ) as file:
                file.write(packet_bytes)

    def transmit(self):
        logger.debug(f"[+] Started transmitter for {self.endpoint}:{self.port}")
        while True:
            # grab a list of all packets and sort them oldest to newest
            packet_list = os.listdir(path=f"{df.CLIENT_DIR}/{self.tx_path}/")
            packet_list.sort()
            for packet in packet_list:
                # check if the transmit address exists
                if self._get_destination()[0] == '':
                    logger.error 
                packet_path = f"{df.CLIENT_DIR}/{self.tx_path}/{packet}"
                with open(file=packet_path, mode="rb") as file:
                    packet_bytes = file.read()

                logger.trace(
                    f"[+] Transmitting {len(packet_bytes)} bytes from packet {self.tx_path}/{packet} to {self._get_destination()}"
                )
                self.send(data=packet_bytes)
                os.remove(packet_path)
