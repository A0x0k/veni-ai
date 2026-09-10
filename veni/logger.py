"""
Log config for Veni AI.
"""

import logging
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _build_file_handler(log_file: Path) -> RotatingFileHandler | None:
    try:
        return RotatingFileHandler(
            log_file,
            maxBytes=2_000_000,
            backupCount=3,
            encoding="utf-8",
        )
    except (PermissionError, OSError):
        return None


LOG_DIR = Path.home() / ".veni-chatbot" / "logs"
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE = LOG_DIR / "veni.log"
except (PermissionError, OSError):
    LOG_DIR = Path(tempfile.gettempdir())
    LOG_FILE = LOG_DIR / "veni.log"

logger = logging.getLogger("veni")
if not logger.handlers:
    file_handler = _build_file_handler(LOG_FILE)
    if file_handler is None:
        fallback_dir = Path(tempfile.gettempdir())
        fallback_dir.mkdir(parents=True, exist_ok=True)
        LOG_DIR = fallback_dir
        LOG_FILE = fallback_dir / "veni.log"
        file_handler = _build_file_handler(LOG_FILE)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(levelname)s %(name)s: %(message)s")
    )
    if file_handler is not None:
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)
    logger.addHandler(console_handler)
logger.setLevel(logging.INFO)
