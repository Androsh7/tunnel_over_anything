# Base connector class for transmitting and receiving

# Standard libraries
import socket
from typing import Optional

# Project libraries
import src.default as df

# Third-party libraries
from attrs import define, field, validators
from loguru import logger


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
    tx_address: tuple[str, int] = field()

    def receive(self) -> Optional[tuple[bytes, tuple[str, int]]]:
        try:
            data, address = self.sock.recvfrom(df.MAX_RECV_BUFFER)
        except ConnectionRefusedError:
            logger.error(f'Incoming connection refused {self.endpoint}:{self.port}')
            return (None, None)
        print(address)
        return data, address

    def listener_service(self):
        logger.debug(f'[+] Started response listener for {self.endpoint}:{self.port}')
        while True:
            packet_bytes, addr = self.receive()
            # ignore if the receive command failed
            if packet_bytes is None or addr is None:
                logger.error(f'Unable to process empty packet from {addr[0]}:{addr[1]}')
                continue
            else:
                # print the updated server transmit endpoint
                if self.tx_address != addr:
                    if self.tx_address is not None:
                        logger.info(f'server transmit endpoint is changing from {self.tx_address[0]}:{self.tx_address[1]} to {addr[0]}:{addr[1]}')
                    else:
                        logger.info(f'initial server transmit endpoint is set to {addr[0]}:{addr[1]}')
                self.tx_address = addr
            date_string = df.get_datetime()
            logger.trace(
                f'[+] Received {len(packet_bytes)} bytes from {addr[0]}:{addr[1]} writing packet to {self.recv_path}/{date_string}.bin'
            )
            with open(
                file=f'{df.CLIENT_DIR}/{self.recv_path}/{date_string}.bin', mode='wb'
            ) as file:
                file.write(packet_bytes)
