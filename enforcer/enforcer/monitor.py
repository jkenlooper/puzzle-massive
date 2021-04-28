from time import sleep
import logging


def monitor(app):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.info(app)

    while True:
        sleep(5)
        logger.debug("sleeping")
    print("exiting monitor")
