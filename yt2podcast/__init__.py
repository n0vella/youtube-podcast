import logging

from yt2podcast.config import settings

# region: logging
logger = logging.getLogger(__package__)

logging.basicConfig(
    filename=settings.logging.log_file or None,
    level=settings.logging.levels.root,
    format=settings.logging.format,
    datefmt=settings.logging.datefmt,
)

logging.getLogger("werkzeug").setLevel(settings.logging.levels.werkzeug)
logging.getLogger("googleapiclient.discovery").setLevel(settings.logging.levels.yt_api)

logger.info("Starting Youtube2Podcast")
# endregion
