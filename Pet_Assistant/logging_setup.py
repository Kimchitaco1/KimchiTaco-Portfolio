import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(logs_dir):
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "catvis.log")

    logger = logging.getLogger("catvis")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=512_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )

    logger.addHandler(file_handler)
    return logger
