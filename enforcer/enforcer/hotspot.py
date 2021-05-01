import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HOTSPOT_EXPIRE = 30


class HotSpot:
    ""

    def __init__(self, redis_connection, rtree_idx):
        self.redis_connection = redis_connection
        self.rtree_idx = rtree_idx

    def handle_message(self, message):
        "enforcer_hotspot:{puzzle} {user}:{piece}:{x}:{y}"
        if message.get("type") != "message":
            return
        channel = message.get("channel", b"").decode()
        data = message.get("data", b"").decode()
        logger.debug(data)
        if not data:
            logger.debug("hotspot no data?")
            return
        (user, piece, x, y) = map(int, data.split(":"))
        puzzle = int(channel.split(":")[1])
        self.process(user, puzzle, piece, x, y)

    def process(self, user, puzzle, piece, x, y):
        # TODO: Handle hotspot by overlaying the actual piece mask on a region
        # of the table.

        # Record hot spot (not exact)
        # TODO: hot spot region should be based on piece size and puzzle size
        xr = x - (x % 40)
        yr = y - (y % 40)
        hotspot_area_key = "hotspot:{puzzle}:{user}:{x}:{y}".format(
            puzzle=puzzle,
            user=user,
            x=xr,
            y=yr,
        )
        hotspot_count = self.redis_connection.incr(hotspot_area_key)
        logger.debug(f"process data for hotspot {puzzle} {xr},{yr} {hotspot_count}")
        nearest = list(self.rtree_idx.nearest([x, y], 2))
        logger.debug(f"nearest {nearest}")
        self.redis_connection.expire(hotspot_area_key, HOTSPOT_EXPIRE)
