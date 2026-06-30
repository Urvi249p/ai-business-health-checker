"""
logger.py — app-wide logger using loguru.

Why loguru over Python's built-in logging?
  - One import, no handler setup, works out of the box
  - Coloured output in terminal during development
  - Same API everywhere: logger.info(), logger.error(), etc.

Usage anywhere in the project:
    from src.utils.logger import logger
    logger.info("Job started", job_id=job_id)
    logger.error(f"Job {job_id} failed: {e}")
"""

import sys
from loguru import logger
from src.config.settings import settings

# Remove the default loguru handler (it has its own format)
logger.remove()

# Add our handler — writes to stdout with timestamp + level + message
logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
    colorize=True,
)