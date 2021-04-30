import datetime
from time import sleep
import logging

from api.tools import get_redis_connection
import enforcer.hotspot


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

TTL = datetime.timedelta(seconds=30)


class Process:
    ""

    def __init__(self, config, puzzle):
        self.config = config
        self.puzzle = puzzle
        self.pubsub = get_redis_connection(self.config, decode_responses=False).pubsub(
            ignore_subscribe_messages=False
        )
        self.redis_connection = get_redis_connection(
            self.config, decode_responses=False
        )

    def start(self):
        logger.debug("start process")
        print("start process")
        now = datetime.datetime.now()
        end = now + TTL
        hotspot = enforcer.hotspot.HotSpot(self.redis_connection)
        self.pubsub.subscribe(
            **{f"enforcer_hotspot:{self.puzzle}": hotspot.handle_message}
        )
        while now < end:
            now = datetime.datetime.now()
            self.pubsub.get_message()
            sleep(3)
            logger.debug("waiting")
        self.pubsub.unsubscribe(f"enforcer_hotspot:{self.puzzle}")
        logger.debug("finish process")
