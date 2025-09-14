"""Handles running the simultaneous processes responsible for the tunnel_over_anything client"""

# Standard libraries
import asyncio
import argparse
import os
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

# Third-party libraries
from loguru import logger

# Project libraries
import src.default as df
from src.client import ClientConnector
from src.load_config import Config
from src.packet_converter import PacketConverter
from src.packet_queue import PacketQueue
from src.server import ServerConnector


def auto_restart_service(service: Callable[[], None], name: str) -> Callable[[], None]:
    """Automatically restarts the function if an exception is thrown

    Args:
        service: function or method to automatically restart
        name: Name of the service (for logging only)
    """

    def wrapped():
        try:
            service()
        except Exception as e:
            logger.error(f"[{name}] Crashed: {e}\n{traceback.format_exc()}")
        else:
            logger.error(f"[{name}] Exited cleanly, restarting...")

    return wrapped


def main():
    """Main entry point for the tunnel_over_anything client application"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Tunnel over Anything client application"
    )
    parser.add_argument(
        "--config",
        "-c",
        help="Path to the config file",
        default=f"{df.CLIENT_DIR}/config.toml",
        required=False,
    )
    args = parser.parse_args()

    # Load config
    config = Config.load_config(file_path=args.config.strip())

    # Set the log format
    logger.remove()
    logger.add(
        sys.stderr,
        format="<level>{time:YYYY-MM-DD HH:mm:ss} | {level: <5} | {message}</level>",
        colorize=True,
        level=config.log_level,
    )

    # Create queues
    client_to_converter = PacketQueue(queue_name="client_to_converter")
    converter_to_client = PacketQueue(queue_name="converter_to_client")
    server_to_converter = PacketQueue(queue_name="server_to_converter")
    converter_to_server = PacketQueue(queue_name="converter_to_server")

    # Configure sub-processes
    client = ClientConnector(
        config=config.client,
        to_converter=client_to_converter,
        from_converter=converter_to_client,
    )
    server = ServerConnector(
        config=config.server,
        to_converter=server_to_converter,
        from_converter=converter_to_server,
    )
    packet = PacketConverter(
        config=config.packet,
        to_client=converter_to_client,
        from_client=client_to_converter,
        to_server=converter_to_server,
        from_server=server_to_converter,
    )

    # Start process workers
    executor = ThreadPoolExecutor(max_workers=6)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # create threads
    loop.run_in_executor(
        executor,
        auto_restart_service(client.transmit_service, name="client-transmitter"),
    )
    loop.run_in_executor(
        executor, auto_restart_service(client.listener_service, name="client-listener")
    )
    loop.run_in_executor(
        executor,
        auto_restart_service(server.transmit_service, name="server-transmitter"),
    )
    loop.run_in_executor(
        executor, auto_restart_service(server.listener_service, name="server-listener")
    )
    loop.run_in_executor(
        executor, auto_restart_service(packet.assembler_service, name="packet-assembler")
    )
    loop.run_in_executor(
        executor,
        auto_restart_service(packet.disassembler_service, name="packet-disassembler"),
    )

    # run loop until stopped
    try:
        loop.run_forever()
    finally:
        logger.info("Shutting down Tunnel over Anything")
        deleted_file_count = 0
        for directory in df.DIRECTORY_PATHS:
            for file in os.listdir(path=f"{df.CLIENT_DIR}/{directory}"):
                file_path = f"{df.CLIENT_DIR}/{directory}/{file}"
                if not os.path.isfile(file_path) or not file_path.endswith(".bin"):
                    continue
                logger.debug(f"Deleting file {file_path}")
                os.remove(path=file_path)
                deleted_file_count += 1
        if deleted_file_count > 0:
            logger.info(f"Deleted {deleted_file_count} binary files")


if __name__ == "__main__":
    main()
