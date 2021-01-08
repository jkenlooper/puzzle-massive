from __future__ import division
from builtins import map
from builtins import zip
from builtins import str
from past.utils import old_div
import os.path
import math
import time
import sys
import random

from flask import current_app
from flask_sse import sse
import requests
from redis.exceptions import WatchError

from api.app import redis_connection
from api.tools import (
    init_karma_key,
    purge_route_from_nginx_cache,
)
from api.constants import COMPLETED, QUEUE_END_OF_LINE, PRIVATE, SKILL_LEVEL_RANGES
from api.piece_mutate import PieceMutateProcess, PieceMutateError

KARMA_POINTS_EXPIRE = 3600  # hour in seconds
RECENT_POINTS_EXPIRE = 7200
PIECE_GROUP_MOVE_MAX_BEFORE_PENALTY = 5
MAX_RECENT_POINTS = 25
MAX_KARMA = 25
MIN_KARMA = int(old_div(MAX_KARMA, 2)) * -1  # -12

skill_level_intervals = list(map(lambda x: x[1], SKILL_LEVEL_RANGES))
skill_level_intervals.sort()


def get_earned_points(pieces, permission=None):
    """
    Return earned points based on skill level of the puzzle. For unlisted
    puzzles the amount is 0 because the puzzle could be a one that was reset.
    Puzzles that have been reset could be scripted by a player in order for them
    to get around the other limits that are controlled by dots.
    """
    if permission is not None and permission == PRIVATE:
        return 0
    for level, max_pieces in enumerate(skill_level_intervals):
        if pieces < max_pieces:
            return level
    return len(skill_level_intervals)


def attempt_piece_movement(ip, user, puzzleData, piece, x, y, r, karma_change):
    try:
        (msg, karma_change) = translate(
            ip, user, puzzleData, piece, x, y, r, karma_change,
        )
    except (PieceMutateError, WatchError):
        current_app.logger.debug(sys.exc_info()[0])
        current_app.logger.warning("piece mutate error")
        err_msg = {
            "msg": "Try again",
            "type": "piecegrouperror",
            "reason": "Conflict with piece group",
            "timeout": 3,
        }
        return (err_msg, 0)
    except:
        current_app.logger.warning("other error {}".format(sys.exc_info()[0]))
        raise

    finally:
        current_app.logger.debug("bump pzq_current")
        pzq_current_key = "pzq_current:{puzzle}".format(puzzle=puzzleData["puzzle"])
        pzq_next_key = "pzq_next:{puzzle}".format(puzzle=puzzleData["puzzle"])
        piece_move_timeout = current_app.config["PIECE_MOVE_TIMEOUT"]
        redis_connection.incr(pzq_current_key, amount=1)
        redis_connection.expire(pzq_current_key, piece_move_timeout + 2)
        redis_connection.expire(pzq_next_key, piece_move_timeout + 2)
    return (msg, karma_change)


def translate(ip, user, puzzleData, piece, x, y, r, karma_change):
    # start = time.perf_counter()

    def publishMessage(msg, karma_change, karma, points=0, complete=False):
        # print(topic)
        # print(msg)
        sse.publish(
            msg,
            type="move",
            channel="puzzle:{puzzle_id}".format(puzzle_id=puzzleData["puzzle_id"]),
        )

        now = int(time.time())

        redis_connection.zadd("pcupdates", {puzzle: now})

        # bump the m_date for this player on the puzzle and timeline
        redis_connection.zadd("timeline:{puzzle}".format(puzzle=puzzle), {user: now})
        redis_connection.zadd("timeline", {user: now})

        # Update player points
        if points != 0 and user != None:
            redis_connection.zincrby(
                "score:{puzzle}".format(puzzle=puzzle), amount=1, value=user
            )
            redis_connection.sadd("batchuser", user)
            redis_connection.sadd("batchpuzzle", puzzle)
            redis_connection.incr("batchscore:{user}".format(user=user), amount=1)
            redis_connection.incr(
                "batchpoints:{puzzle}:{user}".format(puzzle=puzzle, user=user),
                amount=points,
            )
            redis_connection.zincrby("rank", amount=1, value=user)
            points_key = "points:{user}".format(user=user)
            pieces = int(puzzleData["pieces"])
            # Skip increasing dots if puzzle is private
            earns = get_earned_points(pieces, permission=puzzleData.get("permission"))

            karma = int(redis_connection.get(karma_key))
            ## Max out recent points
            # if earns != 0:
            #    recent_points = int(redis_connection.get(points_key) or 0)
            #    if karma + 1 + recent_points + earns < MAX_KARMA:
            #        redis_connection.incr(points_key, amount=earns)
            # Doing small puzzles doesn't increase recent points, just extends points expiration.
            redis_connection.expire(points_key, RECENT_POINTS_EXPIRE)

            karma_change += 1
            # Extend the karma points expiration since it has increased
            redis_connection.expire(karma_key, KARMA_POINTS_EXPIRE)
            # Max out karma
            if karma < MAX_KARMA:
                redis_connection.incr(karma_key)
            else:
                # Max out points
                if earns != 0:
                    recent_points = int(redis_connection.get(points_key) or 0)
                    if recent_points + earns <= MAX_RECENT_POINTS:
                        redis_connection.incr(points_key, amount=earns)

            redis_connection.incr("batchpoints:{user}".format(user=user), amount=earns)

        if complete:
            current_app.logger.info(
                "puzzle {puzzle_id} is complete".format(
                    puzzle_id=puzzleData["puzzle_id"]
                )
            )

            sse.publish(
                "status:{}".format(COMPLETED),
                channel="puzzle:{puzzle_id}".format(puzzle_id=puzzleData["puzzle_id"]),
            )

            r = requests.patch(
                "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                    HOSTAPI=current_app.config["HOSTAPI"],
                    PORTAPI=current_app.config["PORTAPI"],
                    puzzle_id=puzzleData["puzzle_id"],
                ),
                json={
                    "status": COMPLETED,
                    "m_date": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                    "queue": QUEUE_END_OF_LINE,
                },
            )
            if r.status_code != 200:
                raise Exception(
                    "Puzzle details api error when updating puzzle to be complete"
                )
            job = current_app.cleanupqueue.enqueue_call(
                func="api.jobs.convertPiecesToDB.transfer",
                args=(puzzle,),
                kwargs={"delay": 0},
                result_ttl=0,
            )

            purge_route_from_nginx_cache(
                "/chill/site/front/{puzzle_id}/".format(
                    puzzle_id=puzzleData["puzzle_id"]
                ),
                current_app.config.get("PURGEURLLIST"),
            )

        if karma_change:
            sse.publish(
                "{user}:{piece}:{karma}:{karma_change}".format(
                    user=user, piece=piece, karma=karma, karma_change=karma_change
                ),
                type="karma",
                channel="puzzle:{puzzle_id}".format(puzzle_id=puzzleData["puzzle_id"]),
            )

        # end = time.perf_counter()
        # duration = end - start
        # redis_connection.rpush("testdata:translate", duration)
        # return topic and msg mostly for testing
        return (msg, karma_change)

    p = ""
    points = 0
    puzzle = puzzleData["puzzle"]

    karma_key = init_karma_key(redis_connection, puzzle, ip)
    karma = int(redis_connection.get(karma_key))

    pc_puzzle_piece_key = "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece)

    # check if piece can be moved
    (piece_status, has_y) = redis_connection.hmget(pc_puzzle_piece_key, ["s", "y"],)
    if has_y == None:
        err_msg = {"msg": "piece not available", "type": "missing"}
        return (err_msg, 0)

    if piece_status == "1":
        # immovable
        err_msg = {
            "msg": "piece can't be moved",
            "type": "immovable",
            "expires": now + 5,
            "timeout": 5,
        }
        return (err_msg, 0)

    # Restrict piece to within table boundaries
    if x < 0:
        x = 0
    if x > puzzleData["table_width"]:
        x = puzzleData["table_width"]
    if y < 0:
        y = 0
    if y > puzzleData["table_height"]:
        y = puzzleData["table_height"]

    piece_mutate_process = PieceMutateProcess(
        redis_connection,
        puzzle,
        piece,
        x,
        y,
        r,
        piece_count=puzzleData.get("pieces"),
        puzzle_rules=current_app.config["PUZZLE_RULES"],
        piece_move_timeout=current_app.config["PIECE_MOVE_TIMEOUT"],
        piece_join_tolerance=current_app.config["PIECE_JOIN_TOLERANCE"],
    )
    (msg, status) = piece_mutate_process.start()

    if status == "stacked":
        # Decrease karma since stacking
        if (
            len(
                {"all", "karma_stacked"}.intersection(
                    current_app.config["PUZZLE_RULES"]
                )
            )
            > 0
        ):
            if karma > MIN_KARMA:
                redis_connection.decr(karma_key)

        return publishMessage(msg, karma_change, karma)
    elif status == "moved":
        # Decrease karma since moving large group of pieces
        if (
            len(
                {"all", "karma_piece_group_move_max"}.intersection(
                    current_app.config["PUZZLE_RULES"]
                )
            )
            > 0
        ):
            if (
                len(piece_mutate_process.all_other_pieces_in_piece_group)
                > PIECE_GROUP_MOVE_MAX_BEFORE_PENALTY
            ):
                if karma > MIN_KARMA:
                    redis_connection.decr(karma_key)
                    karma_change -= 1
        return publishMessage(msg, karma_change, karma)
    elif status == "joined":
        return publishMessage(msg, karma_change, karma, points=4, complete=False,)

    elif status == "completed":
        return publishMessage(msg, karma_change, karma, points=4, complete=True,)
    else:
        pass

    # TODO: handle failed status
    return publishMessage(msg, karma_change, karma)
