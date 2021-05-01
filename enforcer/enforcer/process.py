import datetime
from time import sleep
import logging

import requests
from rtree import index

from api.constants import ACTIVE, BUGGY_UNLISTED
from api.tools import get_redis_connection
import enforcer.hotspot


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# TODO: set the time to live for an active puzzle to be 5 minutes.
# Set to 30 seconds while developing.
TTL = datetime.timedelta(seconds=30)


def start(config, puzzle):
    """
    Triggered when a puzzle first becomes active from the enforcer_token_request
    channel. This will start a subscription on the specific channels for the
    puzzle to monitor piece movements and update the stacked piece status, piece
    proximity, and hotspots.
    The process will end after a 5 minute time to live (TTL). This frees up
    resources if the puzzle isn't active anymore.
    """
    pubsub = get_redis_connection(config, decode_responses=False).pubsub(
        ignore_subscribe_messages=False
    )
    redis_connection = get_redis_connection(config, decode_responses=False)
    now = datetime.datetime.now()
    end = now + TTL
    logger.debug(f"start process {now}")
    # setup puzzle bbox index
    # create pixelated piece mask if needed
    rtree_idx = create_index(config, redis_connection, puzzle)
    hotspot = enforcer.hotspot.HotSpot(redis_connection, rtree_idx)
    pubsub.subscribe(**{f"enforcer_hotspot:{puzzle}": hotspot.handle_message})
    while now < end:
        now = datetime.datetime.now()
        pubsub.get_message()
        sleep(0.001)
    pubsub.unsubscribe(f"enforcer_hotspot:{puzzle}")
    logger.debug("finish process")

    return puzzle


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
    rtree_idx = index.Index(interleaved=True)

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
        f"http://external-puzzle-massive/newapi/puzzle-pieces/{puzzle_id}/"
    )
    if req.status_code >= 400:
        raise Exception("external-puzzle-massive api error")
    try:
        result = req.json()
    except ValueError as err:
        raise Exception(f"external-puzzle-massive api error {err}")
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
    for piece in piece_data.get("positions", []):
        pc_id = int(piece["id"])
        if has_updates:
            piece.update(piece_updates.get(pc_id, {}))
        (x, y, w, h) = map(
            int,
            [
                piece["x"],
                piece["y"],
                piece["w"],
                piece["h"],
            ],
        )
        piece_bbox = [x, y, x + w, y + h]
        rtree_idx.insert(pc_id, piece_bbox)
    return rtree_idx
