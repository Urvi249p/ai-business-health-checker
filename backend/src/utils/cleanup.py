import asyncio
import time
from pathlib import Path

from src.config.settings import settings
from src.utils.logger import logger


async def start_cleanup_worker() -> None:
    """Periodically delete old PDF and TXT files from the temp directory."""
    await asyncio.sleep(30)

    while True:
        try:
            temp_dir = Path(settings.TEMP_DIR)
            if temp_dir.exists() and temp_dir.is_dir():
                deleted = 0
                now = time.time()
                for file_path in temp_dir.iterdir():
                    if file_path.suffix.lower() in {".pdf", ".txt"}:
                        try:
                            age = now - file_path.stat().st_mtime
                            if age > 1800:
                                file_path.unlink()
                                deleted += 1
                        except Exception as exc:
                            logger.error(
                                f"Cleanup worker failed to delete {file_path}: {exc}"
                            )
                logger.info(
                    f"Cleanup worker removed {deleted} old files from {temp_dir}"
                )
        except Exception as exc:
            logger.error(f"Cleanup worker encountered an error: {exc}")

        await asyncio.sleep(600)
