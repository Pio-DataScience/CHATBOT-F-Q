import base64
import logging
import mammoth
from pathlib import Path

logger = logging.getLogger(__name__)


def convert_docx_to_html(docx_path: Path) -> str:
    """Convert DOCX file to HTML with embedded images."""
    logger.info("Converting DOCX file: %s", docx_path)

    if not docx_path.exists():
        logger.error("DOCX file does not exist: %s", docx_path)
        raise FileNotFoundError(f"DOCX file not found: {docx_path}")

    file_size = docx_path.stat().st_size
    logger.debug("DOCX file size: %d bytes", file_size)

    def convert_image(image):
        """Convert image to base64 data URL."""
        try:
            logger.debug("Converting image: %s", image.content_type)
            with image.open() as f:
                data = f.read()
                b64 = base64.b64encode(data).decode("utf-8")
                logger.debug("Converted image to base64 (%d bytes)", len(data))
                return {"src": f"data:{image.content_type};base64,{b64}"}
        except Exception as e:
            logger.error("Failed to convert image: %s", e)
            raise

    try:
        with open(docx_path, "rb") as f:
            logger.debug("Reading DOCX file and converting to HTML")
            result = mammoth.convert_to_html(
                f,
                convert_image=mammoth.images.inline(convert_image)
            )

        if result.messages:
            for msg in result.messages:
                if msg.type == "warning":
                    logger.warning("Mammoth warning: %s", msg.message)
                elif msg.type == "error":
                    logger.error("Mammoth error: %s", msg.message)
                else:
                    logger.info("Mammoth message: %s", msg.message)

        html_length = len(result.value)
        logger.info("Successfully converted DOCX to HTML (%d characters)",
                    html_length)
        logger.debug("HTML preview: %s...", result.value[:200])

        return result.value

    except Exception as e:
        logger.error("Failed to convert DOCX file %s: %s", docx_path, e)
        raise
