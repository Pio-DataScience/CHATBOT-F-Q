import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_dir(path: Path):
    """Ensure directory exists, creating parent directories as needed."""
    path = Path(path)
    logger.debug("Ensuring directory exists: %s", path)

    try:
        if path.suffix:  # looks like a file path
            target_dir = path.parent
            logger.debug("Detected file path, creating parent dir: %s",
                         target_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            logger.debug("Creating directory: %s", path)
            path.mkdir(parents=True, exist_ok=True)
        logger.debug("Directory ensured successfully")
    except Exception as e:
        logger.error("Failed to create directory %s: %s", path, e)
        raise


def write_text(path: Path, text: str, encoding="utf-8"):
    """Write text to file, ensuring parent directories exist."""
    path = Path(path)
    logger.info("Writing text to file: %s", path)
    logger.debug("Text length: %d characters", len(text))
    logger.debug("Encoding: %s", encoding)

    try:
        ensure_dir(path)
        path.write_text(text, encoding=encoding)
        logger.info("Successfully wrote file: %s", path)
        logger.debug("File size: %d bytes", path.stat().st_size)
    except Exception as e:
        logger.error("Failed to write file %s: %s", path, e)
        raise
