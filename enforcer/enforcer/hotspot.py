import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class HotSpot:
    ""

    def __init__(self, redis_connection):
        self.redis_connection = redis_connection

    def handle_message(self, message):
        logger.debug("process puzzle stuff")
        logger.debug(message)
        data = message.get("data", b"").decode()
        logger.debug(data)
        self.process(data)

    def process(self, data):
        # TODO: Handle hotspot by overlaying the actual piece mask on a region
        # of the table.
        logger.debug(f"process data {data}")
