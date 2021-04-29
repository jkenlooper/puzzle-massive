import logging

logger = logging.getLogger("hotspot")
logger.setLevel(logging.DEBUG)


class HotSpot:
    ""

    def __init__(self, redis_connection):
        self.redis_connection = redis_connection

    def handle_message(self, message):
        logger.debug(message)
        # TODO: Handle hotspot by overlaying the actual piece mask on a region
        # of the table.
