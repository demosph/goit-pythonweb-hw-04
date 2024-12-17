import argparse
import asyncio
from aioshutil import copyfile
from aiopath import AsyncPath
import logging
from asyncio import gather, wait_for, TimeoutError

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Parse command-line arguments.
def parse_args():
    parser = argparse.ArgumentParser(description="Copy files by extension asynchronously")
    parser.add_argument("-s", "--source", type=str, required=True, help="Source folder")
    parser.add_argument("-d", "--destination", type=str, required=True, help="Destination folder")
    return parser.parse_args()

# Recursively reads the source folder and copies files to destination folder sorted by extension.
async def read_folder(source: AsyncPath, destination: AsyncPath):
    if await source.is_dir():
        tasks = [read_folder(child, destination) async for child in source.iterdir()]
        await gather(*tasks)
    else:
        file_extension = source.suffix.lstrip(".")
        if file_extension:
            await copy_file(source, destination, file_extension)
        else:
            logger.warning(f"File '{source}' has no extension. Skipping.")

# Copies a file to a subfolder in the destination directory based on its extension.
async def copy_file(source: AsyncPath, destination: AsyncPath, file_extension: str):
    new_folder = destination / file_extension
    try:
        await new_folder.mkdir(exist_ok=True, parents=True)
        await wait_for(copyfile(source, new_folder / source.name), timeout=10)
        logger.info(f"Copied '{source}' to '{new_folder / source.name}'.")
    except TimeoutError:
        logger.error(f"Timeout copying '{source}'. File skipped.")

# Main function to parse arguments and initiate file reading and copying.
async def main():
    args = parse_args()
    source, destination = AsyncPath(args.source), AsyncPath(args.destination)

    # Create destination directory if it doesn't exist
    if not await destination.exists():
        await destination.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created destination directory: {destination}")

    logger.info(f"Starting file copy. Source: {source}, Destination: {destination}")
    await read_folder(source, destination)
    logger.info("File copying completed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
