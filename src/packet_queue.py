"""Creates a PacketQueue class for packets to be sent/received/processed"""

# Standard libraries
from collections import deque

# Third-party libraries
from attrs import define, field, validators
from loguru import logger


@define
class PacketQueue:
    """Defines the packet queue class for storing packets to be sent/received/processed"""

    _queue: deque = field(
        validator=validators.instance_of(deque),
    )
    queue_name: str = field(
        validator=validators.instance_of(str),
    )

    def __init__(self, queue_name: str, max_size: int = 100):
        self._queue = deque(maxlen=max_size)
        self.queue_name = queue_name
        logger.debug(f"Initialized {self.queue_name} queue with max size {max_size}")

    def __str__(self):
        return self.queue_name

    def is_empty(self) -> bool:
        """Checks if the queue is empty

        Returns:
            True if the queue is empty, False otherwise
        """
        return len(self._queue) == 0

    def enqueue(self, packet: bytes):
        """Adds a packet to the end of the queue

        Args:
            packet: The packet to add to the queue
        """
        try:
            self._queue.append(packet)
            logger.trace(
                f"Enqueued packet to {self.queue_name} queue. Current size: {len(self._queue)}"
            )
        except IndexError:
            logger.error(
                f"Failed to enqueue packet to {self.queue_name} queue: Queue is full"
            )

    def dequeue(self) -> bytes | None:
        """Removes and returns a packet from the front of the queue

        Returns:
            The packet at the front of the queue, or None if the queue is empty
        """
        if self._queue:
            packet = self._queue.popleft()
            logger.trace(
                f"Dequeued packet from {self.queue_name} queue. Current size: {len(self._queue)}"
            )
            return packet
        else:
            logger.error(f"Tried to dequeue from empty {self.queue_name} queue")
            return None
