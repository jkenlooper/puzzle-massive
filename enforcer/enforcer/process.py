import datetime
from time import sleep
import logging

from api.tools import get_redis_connection
import enforcer.hotspot


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

TTL = datetime.timedelta(seconds=30)


def start(config, puzzle):
    pubsub = get_redis_connection(config, decode_responses=False).pubsub(
        ignore_subscribe_messages=False
    )
    redis_connection = get_redis_connection(config, decode_responses=False)
    print("start process")
    now = datetime.datetime.now()
    end = now + TTL
    logger.debug(f"start process {now}")
    hotspot = enforcer.hotspot.HotSpot(redis_connection)
    pubsub.subscribe(**{f"enforcer_hotspot:{puzzle}": hotspot.handle_message})
    while now < end:
        now = datetime.datetime.now()
        pubsub.get_message()
        sleep(3)
        logger.debug("waiting")
    pubsub.unsubscribe(f"enforcer_hotspot:{puzzle}")
    logger.debug("finish process")

    return puzzle
