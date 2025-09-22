"""Creates a PacketQueue class for packets to be sent/received/processed"""

# Third-party libraries
from loguru import logger

# Project libraries
from src.default import LEN_BYTES_COUNT

class PacketRingBuffer:
    """Defines a ring buffer for packets to be sent/received/processed"""

    def __init__(self, max_packets: int, max_packet_size: int, queue_name: str):
        self.queue_name = queue_name
        self.max_packets = max_packets
        self.max_packet_size = max_packet_size
        self.buffer = bytearray(max_packets * max_packet_size)
        self.write_ptr = 0
        self.read_ptr = 0

    def is_empty(self) -> bool:
        """Checks if the ring buffer is empty

        Returns:
            True if the buffer is empty, False otherwise
        """
        return self.read_ptr == self.write_ptr

    def put(self, packet: bytes):
        """Adds a packet to the ring buffer

        Args:
            packet: The packet to add to the buffer
        """
        # Check if packet size exceeds max_packet_size
        if len(packet) > self.max_packet_size - LEN_BYTES_COUNT:
            logger.warning(
                f"[{self.queue_name}] Packet exceeds max_packet_size ({self.max_packet_size} bytes). Packet will be dropped."
            )
            return None

        # Check if buffer will become full after adding packet
        if self.write_ptr + self.max_packet_size == self.read_ptr:
            logger.warning(
                f"[{self.queue_name}] is full. Dropping latest packet"
            )
            return None

        len_bytes = len(packet).to_bytes(LEN_BYTES_COUNT, byteorder="big")
        self.buffer[
            self.write_ptr : self.write_ptr + len(packet) + LEN_BYTES_COUNT
        ] = (len_bytes + packet)
        self.write_ptr = self.write_ptr + self.max_packet_size
        if self.write_ptr >= self.max_packets * self.max_packet_size:
            self.write_ptr = 0

    def get(self) -> bytes | None:
        """Removes and returns a packet from the ring buffer

        Returns:
            The packet at the read pointer, or None if the buffer is empty
        """
        # Check if buffer is empty
        if self.is_empty():
            return None

        len_bytes = self.buffer[self.read_ptr : self.read_ptr + LEN_BYTES_COUNT]
        packet_length = int.from_bytes(len_bytes, byteorder="big")
        packet_bytes = self.buffer[
            self.read_ptr + LEN_BYTES_COUNT : self.read_ptr + LEN_BYTES_COUNT + packet_length
        ]
        self.read_ptr = self.read_ptr + self.max_packet_size
        if self.read_ptr >= self.max_packets * self.max_packet_size:
            self.read_ptr = 0
        return packet_bytes

    def clear(self):
        """Clears the ring buffer"""
        self.write_ptr = 0
        self.read_ptr = 0
        self.buffer = bytearray(self.max_packets * self.max_packet_size * b"\x00")
        logger.debug("Cleared ring buffer")

    def __str__(self):
        return self.queue_name
