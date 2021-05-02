import time
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HOTSPOT_EXPIRE = 30


class HotSpot:
    ""

    def __init__(self, redis_connection, hotspot_idx, piece_properties):
        self.redis_connection = redis_connection
        self.hotspot_idx = hotspot_idx
        self.piece_properties = piece_properties
        self.hotspot_init_time = time.time()

    def handle_message(self, message):
        "enforcer_hotspot:{puzzle} {user}:{piece}:{x}:{y}"
        if message.get("type") != "message":
            return
        channel = message.get("channel", b"").decode()
        data = message.get("data", b"").decode()
        if not data:
            logger.debug("hotspot no data?")
            return
        (user, piece, x, y) = map(int, data.split(":"))
        puzzle = int(channel.split(":")[1])
        self.process(user, puzzle, piece, x, y)

    def process(self, user, puzzle, piece, x, y):
        piece_bbox = [
            x,
            y,
            x + self.piece_properties[piece]["w"],
            y + self.piece_properties[piece]["h"],
        ]
        # The hotspot_id is time based so it can be removed when it gets old.
        hotspot_id = int((time.time() - self.hotspot_init_time) * 1000)
        hotspot_expire_id = hotspot_id - (HOTSPOT_EXPIRE * 1000)

        overlapping_pieces = []
        for item in self.hotspot_idx.intersection(piece_bbox, objects=True):
            if item.id < hotspot_expire_id:
                self.hotspot_idx.delete(item.id, item.bbox)
                continue
            if item.object[0] != user:
                continue
            overlapping_pieces.append(item.object[1])

        # TODO: Handle hotspot by overlaying the actual piece mask with each
        # found overlapping piece.

        hotspot_piece_key = f"hotspot:{puzzle}:{user}:{piece}"
        hotspot_count = len(overlapping_pieces) + 1
        self.redis_connection.set(hotspot_piece_key, hotspot_count, ex=HOTSPOT_EXPIRE)
        self.hotspot_idx.insert(hotspot_id, piece_bbox, [user, piece])
        logger.debug(f"hotspot recorded {hotspot_piece_key} {hotspot_count}")
