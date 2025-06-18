# Handles running the simultaneous processes responsible for the tunnel_over_anything client

# Standard libraries
import asyncio
import sys
import os
from concurrent.futures import ProcessPoolExecutor

# Third-party libraries
from loguru import logger
from src.client import ClientConnector
from src.server import ServerConnector
from src.load_config import Config

# Project libraries
import src.default as df
from src.packet_converter import PacketConverter

if __name__ == "__main__":
    # Load config
    config = Config.load_config()

    # Set the log format
    logger.remove()
    logger.add(sys.stderr, format="<level>| {level: <5} | {message}</level>", colorize=True, level = config.log_level)

    # Set the log level
    #logger.configure(handlers=[{"sink": sys.stderr, "level": config.log_level}])

    # Create sub-directories if they don't exist
    for directory in df.DIRECTORY_PATHS:
        os.makedirs(name=f"{df.CLIENT_DIR}/{directory}/", exist_ok=True)

    # Configure sub-processes
    client = ClientConnector(config=config.client)
    server = ServerConnector(config=config.server)
    packet = PacketConverter(config=config.packet)

    # Start process workers
    try:
        executor = ProcessPoolExecutor(max_workers=6)
        loop = asyncio.new_event_loop()
        loop.run_in_executor(executor, client.transmit_service)
        loop.run_in_executor(executor, client.listener_service)
        loop.run_in_executor(executor, server.transmit_service)
        loop.run_in_executor(executor, server.listener_service)
        loop.run_in_executor(executor, packet.assemble_packets)
        loop.run_in_executor(executor, packet.disassemble_packets)
        loop.run_forever()
    except KeyboardInterrupt:
        logger.debug("User initiated shutdown")    
    finally:
        logger.info("Shutting down Tunnel_Over_Anything")
        deleted_file_count = 0
        for directory in df.DIRECTORY_PATHS:
            for file in os.listdir(path=f'{df.CLIENT_DIR}/{directory}'):
                file_path = f'{df.CLIENT_DIR}/{directory}/{file}'
                if not os.path.isfile(file_path) or not file_path.endswith('.bin'):
                    continue
                logger.debug(f'Deleting file {file_path}')
                os.remove(path=file_path)
                deleted_file_count += 1
        if deleted_file_count > 0:
            logger.info(f'Deleted {deleted_file_count} binary files')
