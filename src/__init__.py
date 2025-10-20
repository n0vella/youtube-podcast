import logging
import os

from dotenv import load_dotenv

load_dotenv()


# region: logging
logging_format = (
    os.getenv("LOG_FORMAT") or "%(asctime)s (%(name)s) [%(levelname)s]: %(message)s"
)

logger = logging.getLogger(__package__)

logging.basicConfig(
    filename=os.getenv("LOG_FILE"),
    level=os.getenv("LOG_LEVEL"),
    format=logging_format,
    datefmt="%d/%m/%Y %H:%M:%S",
)

logging.getLogger("werkzeug").setLevel(os.getenv("LOG_LEVEL") or "WARNING")

logger.info("Starting Youtube Podcast")
# endregion
