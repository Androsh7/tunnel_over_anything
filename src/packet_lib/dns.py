"""Allows for the creation of DNS headers with encoded data"""

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
    'QUERY': 0,
    'RESPONSE': 1,
}

DNS_RECORD_TYPES = {
    'A': 1,  # IPv4 address
    'AAAA': 28,  # IPv6 address
    'CNAME': 5,  # Canonical name (alias)
    'MX': 15,  # Mail exchange
    'NS': 2,  # Name server
    'PTR': 12,  # Pointer (reverse DNS)
    'SOA': 6,  # Start of authority
    'TXT': 16,  # Text (SPF, DKIM, etc.)
    'SRV': 33,  # Service locator
    'CAA': 257,  # Certification Authority Authorization
    'ANY': 255,  # Wildcard query for all types
}

DNS_CLASSES = {'IN': 1, 'ANY': 255}  # Internet (standard)  # Match any class

DOMAIN_LIST = [
    'com',
    'org',
    'net',
    'edu',
    'gov',
    'us',
    'uk',
    'ca',
    'de',
    'fr',
    'au',
    'jp',
    'in',
]


def get_random_domain() -> bytes:
    """returns a random domain as bytes for use in a DNS packet
    I.E: ".com" becomes b"\x03com"

    Returns:
        domain as a bytes object
    """
    domain = DOMAIN_LIST[randint(0, len(DOMAIN_LIST)) - 1]
    return b''.join(
        [
            len(domain).to_bytes(length=1, byteorder='big'),
            bytes(domain, encoding='ASCII'),
        ]
    )


def build_query_list(
    data: bytes,
    record_type: Literal[
        'A', 'AAAA', 'CNAME', 'MX', 'NS', 'PTR', 'SOA', 'TXT', 'SRV', 'CAA', 'ANY'
    ] = 'A',
    query_class: Literal['IN', 'ANY'] = 'IN',
) -> list[bytes]:
    """Constructs a list of DNS query packets based on the provided data, record type,
    and query class.

    Args:
        data: The raw data to be included in the DNS query packets. This data
            will be split into chunks of a maximum length defined by `MAX_RECORD_LENGTH`
        record_type: The DNS record type to query
        query_class: The DNS query class

        list: A list of DNS query packets in byte format, each containing the
        trimmed data, a random domain, and the specified record type and query class

    Raises:
        KeyError: If the provided `record_type` or `query_class` is not found in
        `DNS_RECORD_TYPES` or `DNS_CLASSES`, respectively

    Returns:
        list of all queries in byte strings
    """
    i = 0
    queries = []
    while i < len(data):
        trimmed_data = data[i : i + MAX_RECORD_LENGTH]
        queries.append(
            b''.join(
                [
                    b''.join(
                        [
                            len(trimmed_data).to_bytes(length=1, byteorder='big'),
                            trimmed_data,
                            get_random_domain(),
                            b'\x00',
                        ]
                    ),
                    DNS_RECORD_TYPES[record_type].to_bytes(length=2, byteorder='big'),
                    DNS_CLASSES[query_class].to_bytes(length=2, byteorder='big'),
                ]
            )
        )
        i += MAX_RECORD_LENGTH
    return queries


def build_body(
    method: Literal['QUERY', 'RESPONSE'],
    queries: list[bytes] = None,
    answers: list[bytes] = None,
    authority_records: list[bytes] = None,
    additional_records: list[bytes] = None,
):
    """Builds the body of a DNS packet

    Args:
        method: Specifies whether the packet is a query or a response
        queries: A list of query records in byte format
        answers: A list of answer records in byte format
        authority_records: A list of authority records in byte format
        additional_records: A list of additional records in byte format

    Returns:
        The constructed DNS packet body as a byte string
    """
    return b''.join(
        [
            randint(1, 65535).to_bytes(2, byteorder='big'),  # ID
            DNS_METHODS[method].to_bytes(2, byteorder='big'),  # Query/Response flag
            (
                b'\x00\x00'
                if queries is None
                else len(queries).to_bytes(2, byteorder='big')
            ),  # Number of questions
            (
                b'\x00\x00'
                if answers is None
                else (len(answers)).to_bytes(2, byteorder='big')
            ),  # Number of answers
            (
                b'\x00\x00'
                if authority_records is None
                else (len(authority_records)).to_bytes(2, byteorder='big')
            ),  # Number of authority records
            (
                b'\x00\x00'
                if additional_records is None
                else (len(additional_records)).to_bytes(2, byteorder='big')
            ),  # Number of additional records
            b'' if queries is None else b''.join(queries),
            b'' if answers is None else b''.join(answers),
            b'' if authority_records is None else b''.join(authority_records),
            b'' if additional_records is None else b''.join(additional_records),
        ]
    )


def assemble_dns_packet(data: bytes) -> bytes:
    """Assembles a DNS packet from the provided data

    Args:
        data: The raw data to be included in the DNS packet

    Returns:
        The assembled DNS packet in byte format.
    """
    queries = build_query_list(data=data)
    return build_body(method='QUERY', queries=queries)


def disassemble_dns_packet(packet_bytes: bytes) -> Optional[bytes]:
    """Disassembles a DNS packet and extracts data embedded within the DNS queries

    Args:
        packet_bytes: The raw bytes of the DNS packet to be disassembled

    Returns:
        The extracted data from the DNS queries if successful,
        or None if the packet cannot be parsed
    """
    try:
        dns_packet = DNS(packet_bytes)
    except DissectException as e:
        logger.error(f'[disassembler] {e}')
        return None
    data = b''
    for query in dns_packet.queries:
        data_len = int(query.name[0])
        data += query.name[1 : data_len + 1]
    return data
