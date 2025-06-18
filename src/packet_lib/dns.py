# Allows for the creation of DNS headers with encoded data

# Standard libraries
from random import randint
from typing import Literal, Optional

# Third-party libraries
from loguru import logger

# Project libraries
from pypacker.layer567.dns import DNS
from pypacker.pypacker import DissectException

MAX_RECORD_LENGTH = 60

DNS_METHODS = {
    "QUERY": 0,
    "RESPONSE": 1,
}

DNS_RECORD_TYPES = {
    "A": 1,  # IPv4 address
    "AAAA": 28,  # IPv6 address
    "CNAME": 5,  # Canonical name (alias)
    "MX": 15,  # Mail exchange
    "NS": 2,  # Name server
    "PTR": 12,  # Pointer (reverse DNS)
    "SOA": 6,  # Start of authority
    "TXT": 16,  # Text (SPF, DKIM, etc.)
    "SRV": 33,  # Service locator
    "CAA": 257,  # Certification Authority Authorization
    "ANY": 255,  # Wildcard query for all types
}

DNS_CLASSES = {"IN": 1, "ANY": 255}  # Internet (standard)  # Match any class

DOMAIN_LIST = [
    "com",
    "org",
    "net",
    "edu",
    "gov",
    "us",
    "uk",
    "ca",
    "de",
    "fr",
    "au",
    "jp",
    "in",
]


def get_random_domain() -> bytes:
    domain = DOMAIN_LIST[randint(0, len(DOMAIN_LIST)) - 1]
    return b"".join(
        [
            len(domain).to_bytes(length=1, byteorder="big"),
            bytes(domain, encoding="ASCII"),
        ]
    )


def build_query_list(
    data: bytes,
    record_type: Literal[
        "A", "AAAA", "CNAME", "MX", "NS", "PTR", "SOA", "TXT", "SRV", "CAA", "ANY"
    ] = "A",
    query_class: Literal["IN", "ANY"] = "IN",
) -> list[bytes]:
    i = 0
    queries = []
    while i < len(data):
        trimmed_data = data[i : i + MAX_RECORD_LENGTH]
        queries.append(
            b"".join(
                [
                    b"".join(
                        [
                            len(trimmed_data).to_bytes(length=1, byteorder="big"),
                            trimmed_data,
                            get_random_domain(),
                            b"\x00",
                        ]
                    ),
                    DNS_RECORD_TYPES[record_type].to_bytes(length=2, byteorder="big"),
                    DNS_CLASSES[query_class].to_bytes(length=2, byteorder="big"),
                ]
            )
        )
        i += MAX_RECORD_LENGTH
    return queries


def build_body(
    method: Literal["QUERY", "RESPONSE"],
    queries: list[bytes] = [],
    answers: list[bytes] = [],
    authority_records: list[bytes] = [],
    additional_records: list[bytes] = [],
):
    return b"".join(
        [
            randint(1, 65535).to_bytes(2, byteorder="big"),  # ID
            DNS_METHODS[method].to_bytes(2, byteorder="big"),  # Query/Response flag
            len(queries).to_bytes(2, byteorder="big"),  # Number of questions
            (len(answers)).to_bytes(2, byteorder="big"),  # Number of answers
            (len(authority_records)).to_bytes(
                2, byteorder="big"
            ),  # Number of authority records
            (len(additional_records)).to_bytes(
                2, byteorder="big"
            ),  # Number of additional records
            b"".join(queries),
            b"".join(answers),
            b"".join(authority_records),
            b"".join(additional_records),
        ]
    )


def assemble_dns_packet(data: bytes) -> bytes:
    queries = build_query_list(data=data)
    return build_body(method="QUERY", queries=queries)


def disassemble_dns_packet(packet_bytes: bytes) -> Optional[bytes]:
    try:
        dns_packet = DNS(packet_bytes)
    except DissectException as e:
        logger.error(f"[disassembler] {e}")
        return None
    data = b""
    for query in dns_packet.queries:
        data_len = int(query.name[0])
        data += query.name[1 : data_len + 1]
    return data
