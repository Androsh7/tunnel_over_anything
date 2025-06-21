# Handles running the simultaneous processes responsible for the tunnel_over_anything client

# Standard libraries
import asyncio
import os
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor

# Third-party libraries
from loguru import logger

# Project libraries
import src.default as df
from src.client import ClientConnector
from src.load_config import Config
from src.packet_converter import PacketConverter
from src.server import ServerConnector


def auto_restart_service(service, name: str):
    def wrapped():
        while True:
            try:
                service()
            except Exception as e:
                logger.error(f"[{name}] Crashed: {e}\n{traceback.format_exc()}")
            else:
                logger.error(f"[{name}] Exited cleanly, restarting...")

    return wrapped


if __name__ == "__main__":
    # Load config
    config = Config.load_config()

    # Set the log format
    logger.remove()
    logger.add(
        sys.stderr,
        format="<level>{time:YYYY-MM-DD HH:mm:ss} | {level: <5} | {message}</level>",
        colorize=True,
        level=config.log_level,
    )

    # Create sub-directories if they don't exist
    for directory in df.DIRECTORY_PATHS:
        os.makedirs(name=f"{df.CLIENT_DIR}/{directory}/", exist_ok=True)

    # Configure sub-processes
    client = ClientConnector(config=config.client)
    server = ServerConnector(config=config.server)
    packet = PacketConverter(config=config.packet)

    # Start process workers
    try:
        executor = ThreadPoolExecutor(max_workers=6)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # create threads
        loop.run_in_executor(
            executor,
            auto_restart_service(client.transmit_service, "client-transmitter"),
        )
        loop.run_in_executor(
            executor, auto_restart_service(client.listener_service, "client-listener")
        )
        loop.run_in_executor(
            executor,
            auto_restart_service(server.transmit_service, "server-transmitter"),
        )
        loop.run_in_executor(
            executor, auto_restart_service(server.listener_service, "server-listener")
        )
        loop.run_in_executor(
            executor, auto_restart_service(packet.assembler_service, "packet-assembler")
        )
        loop.run_in_executor(
            executor,
            auto_restart_service(packet.disassembler_service, "packet-disassembler"),
        )

        # run loop until stopped
        loop.run_forever()

    except KeyboardInterrupt:
        logger.debug("User initiated shutdown")
    finally:
        logger.info("Shutting down Tunnel_Over_Anything")
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
