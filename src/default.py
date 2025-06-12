# Includes default values and commonly used functions

# Standard libraries
import os
from datetime import datetime

CLIENT_DIR = "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-1])
MAX_RECV_BUFFER = 65535
PROTOCOLS = ["dns"]
DIRECTORY_PATHS = [
    "inbound/raw_capture",
    "inbound/disassembled_packets",
    "outbound/raw_capture",
    "outbound/assembled_packets",
]


def get_datetime() -> str:
    return datetime.now().strftime(r"%Y%m%d%H%M%S%f")
