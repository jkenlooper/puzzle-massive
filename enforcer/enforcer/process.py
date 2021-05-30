import time
import logging
import atexit

from greenlet import getcurrent, greenlet, GreenletExit
import requests
from rtree import index

from api.constants import ACTIVE, BUGGY_UNLISTED
from api.tools import get_redis_connection
import enforcer.hotspot
import enforcer.proximity


logger = logging.getLogger(__name__)

TTL = 300

HOTSPOT_GRID_SIZE = 40


def start(config, puzzle):
    """
    Triggered when a puzzle first becomes active from the enforcer_token_request
    channel. This will start a subscription on the specific channels for the
    puzzle to monitor piece movements and update the stacked piece status, piece
    proximity, and hotspots.
    The process will end after a 5 minute time to live (TTL). This frees up
    resources if the puzzle isn't active anymore.
    """

    logger.setLevel(logging.DEBUG if config["DEBUG"] else logging.INFO)
    process = Process(config, puzzle)
    process.start()
    logger.debug("process start is done")
    process.close()

    return puzzle


class Process(greenlet):
    ""

    def __init__(self, config, puzzle):
        super().__init__()
        self.halt = False
        self.config = config
        self.puzzle = puzzle
        self.pubsub = get_redis_connection(self.config, decode_responses=False).pubsub(
            ignore_subscribe_messages=False
        )
        self.redis_connection = get_redis_connection(
            self.config, decode_responses=False
        )
        self.now = time.time()
        self.end = self.now + TTL

        self.enable_proximity = bool(
            len(
                {"all", "stack_pieces", "max_stack_pieces"}.intersection(
                    self.config["PUZZLE_RULES"]
                )
            )
        )

        if not self.enable_proximity:
            self.redis_connection.delete(f"pcstacked:{puzzle}")

        logger.info(f"Puzzle {puzzle} init now: {self.now}")
        # setup puzzle bbox index
        # create pixelated piece mask if needed
        (puzzle_data, piece_properties, hotspot_idx, proximity_idx, origin_bboxes) = create_index(
            self.config, self.redis_connection, puzzle
        )
        self.hotspot = enforcer.hotspot.HotSpot(
            self.redis_connection,
            hotspot_idx,
            piece_properties,
            self.config,
        )
        if self.enable_proximity:
            self.proximity = enforcer.proximity.Proximity(
                self.redis_connection,
                proximity_idx,
                origin_bboxes,
                puzzle_data,
                piece_properties,
                self.config,
            )

    def update_active_puzzle(self, message):
        "message = base64({puzzle}:{user}:{piece}:{x}:{y}:{token})"
        logger.debug("update_active_puzzle")
        channel = message.get("channel", b"").decode()
        puzzle = int(channel.split(":")[1])
        if self.puzzle == puzzle:
            self.end = time.time() + TTL

    def handle_piece_translate_message(self, message):
        "enforcer_piece_translate:{puzzle} {user}:{piece}:{origin_x}:{origin_y}:{x}:{y}"
        logger.debug("handle_piece_translate_message")
        if message.get("type") != "message":
            return
        channel = message.get("channel", b"").decode()
        data = message.get("data", b"").decode()
        if not data:
            logger.debug("piece_translate no data?")
            return
        (user, piece, origin_x, origin_y, x, y) = map(int, data.split(":"))
        puzzle = int(channel.split(":")[1])

        self.hotspot.process(user, puzzle, piece, x, y)
        if self.enable_proximity:
            self.proximity.process(user, puzzle, piece, origin_x, origin_y, x, y)

    def handle_piece_group_translate_message(self, message):
        "enforcer_piece_group_translate:{puzzle} {user}:{piece}:{x}:{y}_{user}:{piece}:{x}:{y}_..."
        logger.debug("handle_piece_group_translate_message")
        if not self.enable_proximity:
            # At this time only the proximity process uses this information
            return
        if message.get("type") != "message":
            return
        channel = message.get("channel", b"").decode()
        data = message.get("data", b"").decode()
        if not data:
            logger.debug("piece group translate no data?")
            return

        puzzle = int(channel.split(":")[1])
        pieces = list(map(lambda x: list(map(int, x.split(":"))), data.split("_")))
        self.proximity.batch_process(puzzle, pieces)

    def handle_stop(self, message):
        ""
        if message.get("type") != "message":
            return
        logger.info(f"Stopping enforcer process for puzzle {self.puzzle}")
        self.halt = True

    def run(self):
        ""

        logger.debug(f"Puzzle {self.puzzle} run")
        self.pubsub.subscribe(
            **{
                f"enforcer_piece_group_translate:{self.puzzle}": self.handle_piece_group_translate_message,
                f"enforcer_piece_translate:{self.puzzle}": self.handle_piece_translate_message,
                f"enforcer_token_request:{self.puzzle}": self.update_active_puzzle,
                f"enforcer_stop:{self.puzzle}": self.handle_stop,
            }
        )
        atexit.register(self.halt_process)
        try:
            while not self.halt and self.now < self.end:
                self.now = time.time()
                self.pubsub.get_message()
                getcurrent().parent.switch()
        except GreenletExit:
            logger.info(f"{self.puzzle}: Got GreenletExit; quitting")
        finally:
            self.close()
        return "DONE"

    def close(self):
        ""
        self.pubsub.unsubscribe(f"enforcer_piece_group_translate:{self.puzzle}")
        self.pubsub.unsubscribe(f"enforcer_piece_translate:{self.puzzle}")
        self.pubsub.unsubscribe(f"enforcer_token_request:{self.puzzle}")
        self.pubsub.unsubscribe(f"enforcer_stop:{self.puzzle}")
        self.pubsub.close()
        logger.info(f"Finish process on puzzle {self.puzzle}")

    def halt_process(self):
        self.halt = True
        logger.debug("halt process")
        self.close()


def piece_positions_from_line(line):
    d = {}
    for item in line.split(","):
        values = item.split(":")
        if len(values) != 7:
            continue
        pc_id = int(values[1])
        pc = d.get(pc_id, {})
        new_pc = {"x": int(values[2]), "y": int(values[3])}
        if values[5] != "":
            # parent
            new_pc["g"] = int(values[5])
        if values[6] != "":
            # stacked
            new_pc["s"] = int(values[6])
        pc.update(new_pc)
        d[pc_id] = pc
    return d


def create_index(config, redis_connection, puzzle):
    ""
    # TODO: create a hotspot index which will have a grid of bboxes
    # TODO: create other rtree indexes for tracking pieces as needed for
    # proximity and stacking.

    HOSTAPI = config["HOSTAPI"]
    PORTAPI = config["PORTAPI"]

    req = requests.get(f"http://{HOSTAPI}:{PORTAPI}/internal/pz/{puzzle}/details/")
    if req.status_code >= 400:
        raise Exception("puzzle not available")
    try:
        result = req.json()
    except ValueError as err:
        raise Exception(f"puzzle not available {err}")
    if result.get("status") not in (ACTIVE, BUGGY_UNLISTED):
        raise Exception("puzzle not available")
    puzzle_data = result

    puzzle_id = puzzle_data["puzzle_id"]

    req = requests.get(
        f"http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/pieces/"
    )
    if req.status_code >= 400:
        logger.error(f"puzzle {puzzle_id} not available")
        raise Exception(puzzle)
    try:
        result = req.json()
    except ValueError as err:
        logger.error(f"internal api error {err}")
        raise Exception(puzzle)
    adjacent_pieces = {}
    for piece_id, piece_prop in result["immutable_piece_properties"].items():
        adjacent = {}
        for adjacent_piece_id, adjacent_offset in piece_prop["adjacent"].items():
            adjacent[int(adjacent_piece_id)] = adjacent_offset
        adjacent_pieces[int(piece_id)] = adjacent

    req = requests.get(
        f"http://external-puzzle-massive/newapi/puzzle-pieces/{puzzle_id}/"
    )
    if req.status_code >= 400:
        logger.error("external-puzzle-massive api error")
        raise Exception(puzzle)
    try:
        result = req.json()
    except ValueError as err:
        logger.error(f"external-puzzle-massive api error {err}")
        raise Exception(puzzle)
    piece_data = result

    # timestamp here is really a truncated uuid
    stamp = piece_data["timestamp"]
    # pcu:{stamp} is also used in api pieces.py
    pcu_key = f"pcu:{stamp}"
    piece_updates = {}
    for line in redis_connection.lrange(pcu_key, 0, -1):
        line = line.decode()
        piece_updates.update(piece_positions_from_line(line))
    has_updates = bool(len(piece_updates))
    piece_properties = {}

    for piece in piece_data.get("positions", []):
        pc_id = int(piece["id"])
        if has_updates:
            piece.update(piece_updates.get(pc_id, {}))
        for k in ("id", "x", "y", "r", "w", "h", "b", "rotate"):
            # Not tracking "g" and "s" for group and status since they are
            # updated in a different process.
            v = piece.get(k)
            if isinstance(v, str):
                piece[k] = int(v)
        piece["adjacent"] = adjacent_pieces[pc_id]
        piece_properties[pc_id] = piece

    origin_bboxes = {}
    def piecebboxes():
        for piece in piece_properties.values():
            x = piece["x"]
            y = piece["y"]
            w = piece["w"]
            h = piece["h"]
            piece_bbox = [x, y, x + w, y + h]
            origin_bboxes[piece["id"]] = piece_bbox
            yield (piece["id"], piece_bbox, None)

    proximity_idx = index.Index(piecebboxes(), interleaved=True)

    table_width = puzzle_data["table_width"]
    table_height = puzzle_data["table_height"]

    def gridbboxes():
        # TODO: not used at the moment, but might be in the future for something.
        index = 0
        # TODO: add the remainder cells
        # width_remainder = table_width % HOTSPOT_GRID_SIZE
        # height_remainder = table_height % HOTSPOT_GRID_SIZE
        for row in range(0, table_height // HOTSPOT_GRID_SIZE):
            for col in range(0, table_width // HOTSPOT_GRID_SIZE):
                gridbbox = [
                    col * HOTSPOT_GRID_SIZE,
                    row * HOTSPOT_GRID_SIZE,
                    min((col + 1) * HOTSPOT_GRID_SIZE, table_width),
                    min((row + 1) * HOTSPOT_GRID_SIZE, table_height),
                ]
                yield (index, gridbbox, None)
                index = index + 1

    hotspot_idx = index.Index(interleaved=True)

    return puzzle_data, piece_properties, hotspot_idx, proximity_idx, origin_bboxes
