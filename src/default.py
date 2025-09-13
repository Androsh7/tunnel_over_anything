"""Includes default values and commonly used functions"""

# Standard libraries
import os
from datetime import datetime

CLIENT_DIR = "/".join(
    os.path.dirname(os.path.abspath(__file__)).replace("\\", "/").split("/")[:-1]
)
MAX_RECV_BUFFER = 65535
PROTOCOLS = ["dns", "none"]
ENCODING = ["base64", "base85", "none"]
INBOUND_RAW_PATH = "inbound/raw_capture"
INBOUND_PROCESSED_PATH = "inbound/disassembled_packets"
OUTBOUND_RAW_PATH = "outbound/raw_capture"
OUTBOUND_PROCESSED_PATH = "outbound/assembled_packets"
DIRECTORY_PATHS = [
    INBOUND_RAW_PATH,
    INBOUND_PROCESSED_PATH,
    OUTBOUND_RAW_PATH,
    OUTBOUND_PROCESSED_PATH,
]


def get_datetime() -> str:
    """returns the current date as a string:
    <year><month><day><hour><minute><second><millisecond>
    I.E: 20250620100000472991"""
    return datetime.now().strftime(r"%Y%m%d%H%M%S%f")
