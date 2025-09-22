"""Includes default values and commonly used functions"""

# Standard libraries
import os
from datetime import datetime

CLIENT_DIR = "/".join(
    os.path.dirname(os.path.abspath(__file__)).replace("\\", "/").split("/")[:-1]
)
MAX_PACKET_SIZE = 9000  # Maximum UDP packet size
LEN_BYTES_COUNT = 4  # Number of bytes to store the length of each packet (for PacketRingBuffer)
CONNECTOR_TYPES = ["server", "client"]
PROTOCOLS = ["dns", "none"]
ENCODING_TYPES = ["base64", "none"]
