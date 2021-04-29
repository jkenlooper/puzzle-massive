"""Publish - Piece Movement Publish

Usage: publish serve [--config <file>]
       publish --help
       publish --version

Options:
  -h --help         Show this screen.
  --config <file>   Set config file. [default: site.cfg]

Subcommands:
    serve   - Starts a daemon web server.
"""
from __future__ import absolute_import
from __future__ import division
from builtins import str
from builtins import map

from gevent import monkey

monkey.patch_all()

import datetime
import sys
import time
import uuid
import multiprocessing
from docopt import docopt
import os

import gunicorn.app.base
from flask import current_app, make_response, request, json, Flask
from flask.views import MethodView
from flask_sse import sse
from rq import Queue
import requests

from api.flask_secure_cookie import SecureCookie
from api.app import redis_connection
from api.jobs.pieceTranslate import attempt_piece_movement
from api.tools import (
    loadConfig,
    formatBitMovementString,
    init_karma_key,
    files_loader,
)

from api.constants import (
    ACTIVE,
    BUGGY_UNLISTED,
)

# from jobs import pieceMove
from api.user import user_id_from_ip, user_not_banned, increase_ban_time

HOUR = 3600  # hour in seconds
MINUTE = 60  # minute in seconds

MOVES_BEFORE_PENALTY = 12
STACK_PENALTY = 1
HOTSPOT_EXPIRE = 30
HOTSPOT_LIMIT = 10
HOT_PIECE_MOVEMENT_RATE_TIMEOUT = 10
PIECE_MOVEMENT_RATE_TIMEOUT = 100
PIECE_MOVEMENT_RATE_LIMIT = 100

# How many pieces a user can move within this many seconds before being banned.
# Allow 30 pieces to be moved within 13 seconds. Exceeding that rate would
# probably imply that it is being scripted.
PIECE_TRANSLATE_RATE_TIMEOUT = 13
PIECE_TRANSLATE_MAX_COUNT = 30
PIECE_TRANSLATE_BAN_TIME_INCR = 60 * 5
PIECE_TRANSLATE_EXCEEDED_REASON = "Piece moves exceeded {PIECE_TRANSLATE_MAX_COUNT} in {PIECE_TRANSLATE_RATE_TIMEOUT} seconds".format(
    **locals()
)

TOKEN_INVALID_BAN_TIME_INCR = 15


class PublishApp(Flask):
    "Publish App"


def make_app(config=None, database_writable=False, **kw):
    app = PublishApp("publish")
    app.config_file = config

    if config:
        config_file = (
            config if config[0] == os.sep else os.path.join(os.getcwd(), config)
        )
        app.config.from_pyfile(config_file)

    app.config.update(kw, database_writable=database_writable)

    # Cookie secret value will be read from app.config.
    # If it does not exist, an exception will be thrown.
    #
    # You can also set the cookie secret in the SecureCookie initializer:
    # secure_cookie = SecureCookie(app, cookie_secret="MySecret")
    #
    app.secure_cookie = SecureCookie(app, cookie_secret=kw["cookie_secret"])

    app.queries = files_loader("queries")

    # import the views and sockets
    from api.publish import PuzzlePiecesMovePublishView, PuzzlePieceTokenView

    # register the views

    app.add_url_rule(
        "/puzzle/<puzzle_id>/piece/<int:piece>/move/",
        view_func=PuzzlePiecesMovePublishView.as_view("puzzle-pieces-move"),
    )
    app.add_url_rule(
        "/puzzle/<puzzle_id>/piece/<int:piece>/token/",
        view_func=PuzzlePieceTokenView.as_view("puzzle-piece-token"),
    )

    return app


def bump_count(user):
    """
    Bump the count for pieces moved for the user.
    The nginx conf may also have rate limits on this route. The goal here
    is to ban user if the piece movement rate continues to max out at this rate.
    """
    timestamp_now = int(time.time())
    rounded_timestamp = timestamp_now - (timestamp_now % PIECE_TRANSLATE_RATE_TIMEOUT)
    err_msg = {}

    # TODO: optimize the timestamp used here by truncating to last digits based
    # on the expiration of the key.
    piece_translate_rate_key = "ptrate:{user}:{timestamp}".format(
        user=user, timestamp=rounded_timestamp
    )
    if redis_connection.setnx(piece_translate_rate_key, 1):
        redis_connection.expire(piece_translate_rate_key, PIECE_TRANSLATE_RATE_TIMEOUT)
    count = redis_connection.incr(piece_translate_rate_key)
    if count > PIECE_TRANSLATE_MAX_COUNT:
        err_msg = increase_ban_time(user, PIECE_TRANSLATE_BAN_TIME_INCR)
        err_msg["reason"] = PIECE_TRANSLATE_EXCEEDED_REASON

    return err_msg


def get_blockedplayers_err_msg(expires, timeout):
    err_msg = {
        "msg": "Please wait.",
        "type": "blockedplayer",
        "reason": "Too many recent pieces moves from you were not helpful on this puzzle.",
        "expires": expires,
        "timeout": timeout,
    }
    return err_msg


def get_too_many_pieces_in_proximity_err_msg(piece, piecesInProximity):
    err_msg = {
        "msg": "Piece move denied.",
        "type": "proximity",
        "reason": "Too many pieces within proximity of each other.",
        "piece": piece,
        "piecesInProximity": piecesInProximity,
    }
    return err_msg


def get_puzzle_piece_token_key(puzzle, piece):
    return "pctoken:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece)


def get_puzzle_piece_token_queue_key(puzzle, piece):
    return "pqtoken:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece)


def _int_piece_properties(piece_properties):
    ""
    int_props = ("x", "y", "r", "w", "h", "rotate", "g")
    for (k, v) in piece_properties.items():
        if k in int_props:
            if v != None:
                piece_properties[k] = int(v)
    return piece_properties


def _get_adjacent_pieces_list(piece_properties):
    "Get adjacent pieces list"
    return list(
        map(
            int,
            [
                x
                for x in list(piece_properties.keys())
                if x not in ("x", "y", "r", "w", "h", "b", "rotate", "g", "s")
            ],
        )
    )


class PuzzlePieceTokenView(MethodView):
    """
    player gets token after mousedown.  /puzzle/<puzzle_id>/piece/<int:piece>/token/
    """

    decorators = [user_not_banned]

    def get(self, puzzle_id, piece):
        ip = request.headers.get("X-Real-IP")
        user = current_app.secure_cookie.get("user") or user_id_from_ip(
            ip, validate_shared_user=False
        )
        if user == None:
            err_msg = {
                "msg": "Please reload the page.",
                "reason": "The player login was not found.",
                "type": "puzzlereload",
                "timeout": 300,
            }
            response = make_response(json.jsonify(err_msg), 400)
            expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
            current_app.secure_cookie.set("user", "", response, expires=expires)
            current_app.secure_cookie.set("shareduser", "", response, expires=expires)
            return response

        user = int(user)
        mark = request.args.get("mark")
        if not isinstance(mark, str) or len(mark) != 10:
            return make_response(
                json.jsonify(
                    {
                        "msg": "invalid args",
                        "type": "invalid",
                    }
                ),
                400,
            )
        now = int(time.time())

        # start = time.perf_counter()
        pzq_key = "pzq:{puzzle_id}".format(puzzle_id=puzzle_id)
        puzzle = redis_connection.hget(pzq_key, "puzzle")
        if not puzzle:
            current_app.logger.debug("no puzzle; fetch puzzle")
            r = requests.get(
                "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                    HOSTAPI=current_app.config["HOSTAPI"],
                    PORTAPI=current_app.config["PORTAPI"],
                    puzzle_id=puzzle_id,
                ),
            )
            if r.status_code >= 400:
                # 400 if puzzle does not exist
                err_msg = {
                    "msg": "puzzle is not ready at this time. Please reload the page.",
                    "type": "puzzleimmutable",
                }
                return make_response(json.jsonify(err_msg), r.status_code)
            try:
                result = r.json()
            except ValueError as err:
                err_msg = {
                    "msg": "puzzle is not ready at this time. Please reload the page.",
                    "type": "puzzleimmutable",
                }
                return make_response(json.jsonify(err_msg), 500)
            if result.get("status") not in (ACTIVE, BUGGY_UNLISTED):
                err_msg = {
                    "msg": "puzzle is not ready at this time. Please reload the page.",
                    "type": "puzzleimmutable",
                }
                return make_response(json.jsonify(err_msg), 400)
            puzzle = result["id"]

        puzzle = int(puzzle)
        pc_puzzle_piece_key = "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece)
        piece_properties = _int_piece_properties(
            redis_connection.hgetall(pc_puzzle_piece_key)
        )

        if piece_properties.get("y") is None:
            # 400 if puzzle does not exist or piece is not found
            # Only puzzles in ACTIVE state can be mutated
            err_msg = {
                "msg": "puzzle pieces can't be moved at this time. Please reload the page.",
                "type": "puzzleimmutable",
            }
            return make_response(json.jsonify(err_msg), 400)

        if piece_properties.get("s") == "1":
            # immovable
            err_msg = {
                "msg": "piece can't be moved",
                "type": "immovable",
                "expires": now + 5,
                "timeout": 5,
            }
            return make_response(json.jsonify(err_msg), 400)

        # TODO: remove old entries in blockedplayers:{puzzle}
        blockedplayers_for_puzzle_key = "blockedplayers:{puzzle}".format(puzzle=puzzle)
        blockedplayers_expires = redis_connection.zscore(
            blockedplayers_for_puzzle_key, user
        )
        if blockedplayers_expires and blockedplayers_expires > now:
            err_msg = get_blockedplayers_err_msg(
                blockedplayers_expires, blockedplayers_expires - now
            )
            return make_response(json.jsonify(err_msg), 429)

        def move_bit_icon_to_piece(x, y):
            # Claim the piece by showing the bit icon next to it.
            msg = formatBitMovementString(user, x, y)
            sse.publish(
                msg,
                type="move",
                channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_id),
            )

        # Snapshot of adjacent pieces at time of token request
        snapshot_id = None
        adjacent_pieces_list = _get_adjacent_pieces_list(piece_properties)
        adjacent_property_list = ["x", "y", "r", "g", "s", str(piece)]
        pzq_current_key = "pzq_current:{puzzle}".format(puzzle=puzzle)
        results = []
        with redis_connection.pipeline(transaction=False) as pipe:
            for adjacent_piece in adjacent_pieces_list:
                pc_puzzle_adjacent_piece_key = "pc:{puzzle}:{adjacent_piece}".format(
                    puzzle=puzzle, adjacent_piece=adjacent_piece
                )
                pipe.hmget(pc_puzzle_adjacent_piece_key, adjacent_property_list)
            pipe.get(pzq_current_key)
            results = pipe.execute()
        pzq_current = "0"
        if not isinstance(results[-1], list):
            pzq_current = results.pop() or pzq_current
        adjacent_properties = dict(
            zip(
                adjacent_pieces_list,
                map(lambda x: dict(zip(adjacent_property_list, x)), results),
            )
        )
        snapshot = []
        for a_piece, a_props in adjacent_properties.items():
            # skip any that are immovable
            if a_props.get("s") == "1":
                continue
            # skip any that are in the same group
            if a_props.get("g") != None and a_props.get("g") == piece_properties.get(
                "g"
            ):
                continue
            # skip any that don't have offsets (adjacent edge piece)
            if not a_props.get(str(piece)):
                continue
            if a_props.get("g") is None:
                a_props["g"] = ""
            snapshot.append(
                "_".join(
                    [
                        str(a_piece),
                        a_props.get("x", ""),
                        a_props.get("y", ""),
                        a_props.get("r", ""),
                        a_props.get(str(piece), ""),
                        # a_props.get("g")
                    ]
                )
            )

        if len(snapshot):
            snapshot_id = uuid.uuid4().hex[:8]
            snapshot_key = f"snap:{snapshot_id}"
            snapshot.insert(0, pzq_current)
            redis_connection.set(snapshot_key, ":".join(snapshot))
            redis_connection.expire(
                snapshot_key,
                current_app.config["MAX_PAUSE_PIECES_TIMEOUT"]
                + (current_app.config["PIECE_MOVE_TIMEOUT"] + 2),
            )

        validate_token = (
            len({"all", "valid_token"}.intersection(current_app.config["PUZZLE_RULES"]))
            > 0
        )

        TOKEN_LOCK_TIMEOUT = current_app.config["TOKEN_LOCK_TIMEOUT"]
        TOKEN_EXPIRE_TIMEOUT = current_app.config["TOKEN_EXPIRE_TIMEOUT"]
        if not validate_token:

            move_bit_icon_to_piece(piece_properties.get("x"), piece_properties.get("y"))
            response = {
                "token": "---",
                "lock": now + TOKEN_LOCK_TIMEOUT,
                "expires": now + TOKEN_EXPIRE_TIMEOUT,
            }
            if snapshot_id:
                response["snap"] = snapshot_id
            return make_response(json.jsonify(response), 200)

        # Check if user already has a token for this puzzle. This would mean
        # that the user tried moving another piece before the locked piece
        # finished moving.
        existing_token = redis_connection.get(f"t:{mark}")
        if existing_token:
            # Temporary ban the player when clicking a piece and not
            # dropping it before clicking another piece.
            # Ban the user for a few seconds
            err_msg = increase_ban_time(user, TOKEN_LOCK_TIMEOUT)
            err_msg[
                "reason"
            ] = "Concurrent piece movements on this puzzle from the same player are not allowed."
            return make_response(json.jsonify(err_msg), 429)

        piece_token_queue_key = get_puzzle_piece_token_queue_key(puzzle, piece)
        with redis_connection.pipeline(transaction=False) as pipe:
            pipe.zrank(piece_token_queue_key, mark)
            pipe.expire(piece_token_queue_key, TOKEN_LOCK_TIMEOUT + 5)
            (queue_rank, _) = pipe.execute()

        if queue_rank is None:
            # Append this player to a queue for getting the next token. This
            # will prevent the player with the lock from continually locking the
            # same piece.
            with redis_connection.pipeline(transaction=False) as pipe:
                pipe.zadd(piece_token_queue_key, {mark: now})
                pipe.zrank(piece_token_queue_key, mark)
                (_, queue_rank) = pipe.execute()

        # Check if token on piece is in a queue and if the player requesting it
        # is the player that is next. Show an error message if not.
        if queue_rank > 0:
            err_msg = {
                "msg": "Another player is waiting to move this piece",
                "type": "piecequeue",
                "reason": "Piece queue {}".format(queue_rank),
                "expires": now + TOKEN_LOCK_TIMEOUT,
                "timeout": TOKEN_LOCK_TIMEOUT,
            }
            return make_response(json.jsonify(err_msg), 409)

        # Check if token on piece is still owned by another user
        puzzle_piece_token_key = get_puzzle_piece_token_key(puzzle, piece)
        existing_token_and_mark = redis_connection.get(puzzle_piece_token_key)
        if existing_token_and_mark:
            (other_token, other_mark) = existing_token_and_mark.split(":")
            puzzle_and_piece_and_user = redis_connection.get(f"t:{other_mark}")
            # Check if there is a lock on this piece by other user
            if puzzle_and_piece_and_user:
                (
                    other_puzzle,
                    other_piece,
                    other_user,
                ) = puzzle_and_piece_and_user.split(":")
                other_puzzle = int(other_puzzle)
                other_piece = int(other_piece)
                other_user = int(other_user)
                if other_puzzle == puzzle and other_piece == piece:
                    # Other user has a lock on this piece
                    err_msg = {
                        "msg": "Another player is moving this piece",
                        "type": "piecelock",
                        "reason": "Piece locked",
                    }
                    return make_response(json.jsonify(err_msg), 409)

        # This piece is up for grabs since it has been more then 5 seconds since
        # another player has grabbed it.
        token = uuid.uuid4().hex[:8]
        with redis_connection.pipeline(transaction=False) as pipe:
            # Remove player from the piece token queue
            pipe.zrem(piece_token_queue_key, mark)

            pipe.set(
                puzzle_piece_token_key,
                f"{token}:{mark}",
                ex=TOKEN_EXPIRE_TIMEOUT,
            )
            pipe.set(
                f"t:{mark}",
                f"{puzzle}:{piece}:{user}",
                ex=TOKEN_LOCK_TIMEOUT,
            )
            pipe.execute()

        move_bit_icon_to_piece(piece_properties.get("x"), piece_properties.get("y"))

        response = {
            "token": token,
            "lock": now + TOKEN_LOCK_TIMEOUT,
            "expires": now + TOKEN_EXPIRE_TIMEOUT,
        }
        if snapshot_id:
            response["snap"] = snapshot_id
        # end = time.perf_counter()
        # current_app.logger.debug("PuzzlePieceTokenView {}".format(end - start))
        return make_response(json.jsonify(response), 200)


class PuzzlePiecesMovePublishView(MethodView):
    """
    Publish the puzzle piece movement and push it to the redis queue.

    * Check if valid args
    * Validate the token
    * Validate that puzzle and piece exist and are in mutable state

    * Set karma

    * Check if piece move is within bounds
    * Check if piece move is not to a large stacked area

    * Check if karma + points > 0

    * Publish bit movment
    * Start piece translate logic
    """

    ACCEPTABLE_ARGS = set(["x", "y", "r"])

    def patch(self, puzzle_id, piece):
        """
        args:
        x
        y
        r
        """

        def _blockplayer():
            timeouts = current_app.config["BLOCKEDPLAYER_EXPIRE_TIMEOUTS"]
            blocked_count_ip_key = f"blocked:{ip}"
            expire_index = max(0, redis_connection.incr(blocked_count_ip_key) - 1)
            redis_connection.expire(blocked_count_ip_key, timeouts[-1])
            timeout = timeouts[min(expire_index, len(timeouts) - 1)]
            expires = now + timeout
            blockedplayers_for_puzzle_key = "blockedplayers:{puzzle}".format(
                puzzle=puzzle
            )
            # Add the player to the blocked players list for the puzzle and
            # extend the expiration of the key.
            redis_connection.zadd(blockedplayers_for_puzzle_key, {user: expires})
            redis_connection.expire(blockedplayers_for_puzzle_key, timeouts[-1])

            err_msg = get_blockedplayers_err_msg(expires, expires - now)
            sse.publish(
                "{user}:{piece}:{karma}:{karma_change}".format(
                    user=user,
                    piece=piece,
                    karma=karma + recent_points,
                    karma_change=karma_change,
                ),
                type="karma",
                channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_data["puzzle_id"]),
            )
            return make_response(json.jsonify(err_msg), 429)

        ip = request.headers.get("X-Real-IP")
        validate_token = (
            len({"all", "valid_token"}.intersection(current_app.config["PUZZLE_RULES"]))
            > 0
        )
        user = None
        now = int(time.time())

        # validate the args and headers
        args = {}
        xhr_data = request.get_json()
        if xhr_data:
            args.update(xhr_data)
        if request.form:
            args.update(request.form.to_dict(flat=True))

        if len(list(args.keys())) == 0:
            err_msg = {
                "msg": "invalid args",
                "type": "invalid",
                "expires": now + 5,
                "timeout": 5,
            }
            return make_response(json.jsonify(err_msg), 400)
        # check if args are only in acceptable set
        if len(self.ACCEPTABLE_ARGS.intersection(set(args.keys()))) != len(
            list(args.keys())
        ):
            err_msg = {
                "msg": "invalid args",
                "type": "invalid",
                "expires": now + 5,
                "timeout": 5,
            }
            return make_response(json.jsonify(err_msg), 400)
        # validate that all values are int
        for key, value in list(args.items()):
            if not isinstance(value, int):
                try:
                    args[key] = int(value)
                except ValueError:
                    err_msg = {
                        "msg": "invalid args",
                        "type": "invalid",
                        "expires": now + 5,
                        "timeout": 5,
                    }
                    return make_response(json.jsonify(err_msg), 400)
        x = args.get("x")
        y = args.get("y")
        r = args.get("r")
        snapshot_id = request.headers.get("Snap")

        # Token is to make sure puzzle is still in sync.
        # validate the token
        token = request.headers.get("Token")
        if not token:
            err_msg = {
                "msg": "Missing token",
                "type": "missing",
                "expires": now + 5,
                "timeout": 5,
            }
            return make_response(json.jsonify(err_msg), 400)

        mark = request.headers.get("Mark")
        if not mark:
            err_msg = {
                "msg": "Missing mark",
                "type": "missing",
                "expires": now + 5,
                "timeout": 5,
            }
            return make_response(json.jsonify(err_msg), 400)

        # start = time.perf_counter()
        existing_token = redis_connection.get(f"t:{mark}")
        if validate_token and existing_token:
            (m_puzzle, m_piece, m_user) = existing_token.split(":")
            user = int(m_user)
        else:
            user = current_app.secure_cookie.get("user") or user_id_from_ip(
                ip, validate_shared_user=False
            )
            if user is None:
                err_msg = {
                    "msg": "Please reload the page.",
                    "reason": "The player login was not found.",
                    "type": "puzzlereload",
                    "timeout": 300,
                }
                return make_response(json.jsonify(err_msg), 400)
            user = int(user)

        pzq_key = "pzq:{puzzle_id}".format(puzzle_id=puzzle_id)
        pzq_fields = [
            "puzzle",
            "table_width",
            "table_height",
            "permission",
            "pieces",
        ]
        puzzle_data = dict(zip(pzq_fields, redis_connection.hmget(pzq_key, pzq_fields)))
        puzzle = puzzle_data.get("puzzle")
        if puzzle is None:
            req = requests.get(
                "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                    HOSTAPI=current_app.config["HOSTAPI"],
                    PORTAPI=current_app.config["PORTAPI"],
                    puzzle_id=puzzle_id,
                ),
            )
            if req.status_code >= 400:
                err_msg = {"msg": "puzzle not available", "type": "missing"}
                return make_response(json.jsonify(err_msg), req.status_code)
            try:
                result = req.json()
            except ValueError as err:
                err_msg = {"msg": "puzzle not available", "type": "missing"}
                return make_response(json.jsonify(err_msg), 500)
            if result.get("status") not in (ACTIVE, BUGGY_UNLISTED):
                err_msg = {"msg": "puzzle not available", "type": "missing"}
                return make_response(json.jsonify(err_msg), 404)
            puzzle_data = result
            puzzle_data["puzzle"] = result["id"]

            redis_connection.hmset(
                pzq_key,
                {
                    "puzzle": puzzle_data["puzzle"],
                    "table_width": puzzle_data["table_width"],
                    "table_height": puzzle_data["table_height"],
                    "permission": puzzle_data["permission"],
                    "pieces": puzzle_data["pieces"],
                },
            )
            redis_connection.expire(pzq_key, 300)
        else:
            puzzle_data["puzzle"] = int(puzzle_data["puzzle"])
            puzzle_data["table_width"] = int(puzzle_data["table_width"])
            puzzle_data["table_height"] = int(puzzle_data["table_height"])
            puzzle_data["permission"] = int(puzzle_data["permission"])
            puzzle_data["pieces"] = int(puzzle_data["pieces"])
        puzzle = int(puzzle_data["puzzle"])
        puzzle_data["puzzle_id"] = puzzle_id

        puzzle_piece_token_key = get_puzzle_piece_token_key(puzzle, piece)
        validate_token = (
            len({"all", "valid_token"}.intersection(current_app.config["PUZZLE_RULES"]))
            > 0
        )
        if validate_token:
            token_and_mark = redis_connection.get(puzzle_piece_token_key)
            if token_and_mark:
                (valid_token, other_mark) = token_and_mark.split(":")
                # other_user = int(other_user)
                if token != valid_token:
                    err_msg = increase_ban_time(user, TOKEN_INVALID_BAN_TIME_INCR)
                    err_msg["reason"] = "Token is invalid"
                    return make_response(json.jsonify(err_msg), 409)
                if mark != other_mark:
                    err_msg = increase_ban_time(user, TOKEN_INVALID_BAN_TIME_INCR)
                    err_msg["reason"] = "Player is invalid"
                    return make_response(json.jsonify(err_msg), 409)
            else:
                err_msg = {
                    "msg": "Token has expired",
                    "type": "expiredtoken",
                    "reason": "",
                }
                return make_response(json.jsonify(err_msg), 409)

        # Expire the token since it shouldn't be used again
        if validate_token:
            redis_connection.delete(puzzle_piece_token_key)
            redis_connection.delete(f"t:{mark}")

        if (
            len(
                {"all", "piece_translate_rate"}.intersection(
                    current_app.config["PUZZLE_RULES"]
                )
            )
            > 0
        ):
            err_msg = bump_count(user)
            if err_msg.get("type") == "bannedusers":
                return make_response(json.jsonify(err_msg), 429)

        # Check if piece will be moved to within boundaries
        if x and (x < 0 or x > puzzle_data["table_width"]):
            err_msg = {
                "msg": "Piece movement out of bounds",
                "type": "invalidpiecemove",
                "expires": now + 5,
                "timeout": 5,
            }
            return make_response(json.jsonify(err_msg), 400)
        if y and (y < 0 or y > puzzle_data["table_height"]):
            err_msg = {
                "msg": "Piece movement out of bounds",
                "type": "invalidpiecemove",
                "expires": now + 5,
                "timeout": 5,
            }
            return make_response(json.jsonify(err_msg), 400)

        # Check again if piece can be moved and hasn't changed since getting token
        (piece_status, has_y) = redis_connection.hmget(
            "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece),
            ["s", "y"],
        )
        if has_y is None:
            err_msg = {"msg": "piece not available", "type": "missing"}
            return make_response(json.jsonify(err_msg), 404)

        if piece_status == "1":
            # immovable
            err_msg = {
                "msg": "piece can't be moved",
                "type": "immovable",
                "expires": now + 5,
                "timeout": 5,
            }
            return make_response(json.jsonify(err_msg), 400)

        # TODO: publish the piece movement to enforcer so it can track hot spot
        # and piece stacking stuff.
        if (
            len({"all", "hot_spot"}.intersection(current_app.config["PUZZLE_RULES"]))
            > 0
        ):
            redis_connection.publish(
                "enforcer_hotspot", f"{user}:{puzzle}:{piece}:{x}:{y}"
            )

        points_key = "points:{user}".format(user=user)
        recent_points = int(redis_connection.get(points_key) or "0")

        karma_key = init_karma_key(redis_connection, puzzle, ip, current_app.config)
        karma = int(redis_connection.get(karma_key))
        karma_change = 0
        current_app.logger.debug(
            f"user: {user} ip: {ip} karma: {karma} recent_points {recent_points}"
        )

        if (
            len(
                {"all", "puzzle_open_rate"}.intersection(
                    current_app.config["PUZZLE_RULES"]
                )
            )
            > 0
        ):
            # Decrease recent points if this is a new puzzle that user hasn't moved pieces on yet in the last hour
            pzrate_key = "pzrate:{user}:{today}".format(
                user=user, today=datetime.date.today().isoformat()
            )
            if redis_connection.sadd(pzrate_key, puzzle) == 1:
                # New puzzle that player hasn't moved a piece on in the last hour.
                redis_connection.expire(pzrate_key, HOUR)
                if recent_points > 0:
                    redis_connection.decr(points_key)

        if (
            len(
                {"all", "piece_move_rate"}.intersection(
                    current_app.config["PUZZLE_RULES"]
                )
            )
            > 0
        ):
            # Decrease karma if piece movement rate has passed threshold
            pcrate_key = f"pcrate:{puzzle}:{user}"
            moves = redis_connection.incr(pcrate_key)
            redis_connection.expire(pcrate_key, PIECE_MOVEMENT_RATE_TIMEOUT)
            if moves > PIECE_MOVEMENT_RATE_LIMIT:
                if karma > 0:
                    karma = redis_connection.decr(karma_key)
                karma_change -= 1

        if (
            len({"all", "hot_piece"}.intersection(current_app.config["PUZZLE_RULES"]))
            > 0
        ):
            # Decrease karma when moving the same piece multiple times within
            # a minute.
            hotpc_key = f"hotpc:{puzzle}:{user}:{piece}"
            recent_move_count = redis_connection.incr(hotpc_key)
            redis_connection.expire(hotpc_key, HOT_PIECE_MOVEMENT_RATE_TIMEOUT)

            if recent_move_count > MOVES_BEFORE_PENALTY:
                if karma > 0:
                    karma = redis_connection.decr(karma_key)
                karma_change -= 1

        if (
            len({"all", "hot_spot"}.intersection(current_app.config["PUZZLE_RULES"]))
            > 0
        ):
            # Record hot spot (not exact)
            # TODO: hot spot region should be based on piece size and puzzle size
            hotspot_area_key = "hotspot:{puzzle}:{user}:{x}:{y}".format(
                puzzle=puzzle,
                user=user,
                x=x - (x % 40),
                y=y - (y % 40),
            )
            hotspot_count = redis_connection.incr(hotspot_area_key)
            redis_connection.expire(hotspot_area_key, HOTSPOT_EXPIRE)
            if hotspot_count > HOTSPOT_LIMIT:
                if karma > 0:
                    karma = redis_connection.decr(karma_key)
                karma_change -= 1

        if karma_change < 0:
            # Decrease recent points for a piece move that decreased karma
            if recent_points > 0 and karma_change < 0:
                recent_points = redis_connection.decr(points_key)
            if karma + recent_points <= 0:
                return _blockplayer()

        piece_move_timeout = current_app.config["PIECE_MOVE_TIMEOUT"]

        # Use a custom built and managed queue to prevent multiple processes
        # from running the attempt_piece_movement concurrently on the same
        # puzzle.
        pzq_current_key = "pzq_current:{puzzle}".format(puzzle=puzzle)
        pzq_next_key = "pzq_next:{puzzle}".format(puzzle=puzzle)
        # The attempt_piece_movement bumps the pzq_current by 1
        pzq_next = redis_connection.incr(pzq_next_key, amount=1)
        # Set the expire in case it fails to reach expire in attempt_piece_movement.
        redis_connection.expire(pzq_current_key, piece_move_timeout + 2)
        redis_connection.expire(pzq_next_key, piece_move_timeout + 2)

        attempt_count = 0
        attempt_timestamp = time.time()
        timeout = attempt_timestamp + piece_move_timeout
        while attempt_timestamp < timeout:
            pzq_current = int(redis_connection.get(pzq_current_key) or "0")
            if pzq_current == pzq_next - 1:
                try:
                    snapshot_msg = None
                    snapshot_karma_change = False
                    if snapshot_id:
                        snapshot_key = f"snap:{snapshot_id}"
                        snapshot = redis_connection.get(snapshot_key)
                        if snapshot:
                            snapshot_list = snapshot.split(":")
                            snapshot_pzq = int(snapshot_list.pop(0))
                            if snapshot_pzq != pzq_current:
                                # Check if any adjacent pieces are within range of x, y, r
                                # Within that list check if any have moved
                                # With the first one that has moved that was within range attempt piece movement on that by using adjusted x, y, r
                                snaps = list(map(lambda x: x.split("_"), snapshot_list))
                                adjacent_piece_ids = list(
                                    map(lambda x: int(x[0]), snaps)
                                )
                                adjacent_piece_props_snaps = list(
                                    map(lambda x: x[1:], snaps)
                                )
                                property_list = [
                                    "x",
                                    "y",
                                    "r",
                                    # "g"
                                ]
                                results = []
                                with redis_connection.pipeline(
                                    transaction=True
                                ) as pipe:
                                    for adjacent_piece_id in adjacent_piece_ids:
                                        pc_puzzle_adjacent_piece_key = (
                                            f"pc:{puzzle}:{adjacent_piece_id}"
                                        )
                                        pipe.hmget(
                                            pc_puzzle_adjacent_piece_key,
                                            property_list,
                                        )
                                    results = pipe.execute()
                                for (a_id, snapshot_adjacent, updated_adjacent,) in zip(
                                    adjacent_piece_ids,
                                    adjacent_piece_props_snaps,
                                    results,
                                ):
                                    updated_adjacent = list(
                                        map(
                                            lambda x: x if isinstance(x, str) else "",
                                            updated_adjacent,
                                        )
                                    )
                                    adjacent_offset = snapshot_adjacent.pop()
                                    if (
                                        snapshot_adjacent != updated_adjacent
                                    ) and adjacent_offset:
                                        (a_offset_x, a_offset_y) = map(
                                            int, adjacent_offset.split(",")
                                        )
                                        (a_snap_x, a_snap_y) = map(
                                            int, snapshot_adjacent[:2]
                                        )
                                        # Check if the x,y is within range of the adjacent piece that has moved
                                        # TODO: use the pieces adjacent piece range bbox when setting piece_join_tolerance
                                        piece_join_tolerance = current_app.config[
                                            "PIECE_JOIN_TOLERANCE"
                                        ]
                                        if (
                                            abs((a_snap_x + a_offset_x) - x)
                                            <= piece_join_tolerance
                                            and abs((a_snap_y + a_offset_y) - y)
                                            <= piece_join_tolerance
                                        ):
                                            (a_moved_x, a_moved_y) = map(
                                                int, updated_adjacent[:2]
                                            )
                                            # Decrease pzq_current since it is moving an extra piece out of turn
                                            redis_connection.decr(
                                                pzq_current_key, amount=1
                                            )
                                            (
                                                snapshot_msg,
                                                snapshot_karma_change,
                                            ) = attempt_piece_movement(
                                                ip,
                                                user,
                                                puzzle_data,
                                                piece,
                                                a_moved_x + a_offset_x,
                                                a_moved_y + a_offset_y,
                                                r,
                                                karma_change,
                                                karma,
                                            )
                                            break
                except:
                    pzq_current = int(redis_connection.get(pzq_current_key) or "0")
                    if pzq_current == pzq_next - 1:
                        # skip this piece move attempt
                        redis_connection.incr(pzq_current_key, amount=1)
                    current_app.logger.warning(
                        "results123 other error {}".format(sys.exc_info()[0])
                    )
                    raise

                (msg, karma_change) = attempt_piece_movement(
                    ip,
                    user,
                    puzzle_data,
                    piece,
                    x,
                    y,
                    r,
                    karma_change or snapshot_karma_change,
                    karma,
                )
                if isinstance(snapshot_msg, str) and isinstance(msg, str):
                    msg = snapshot_msg + msg
                break
            current_app.logger.debug(f"pzq_current is {pzq_current}")
            attempt_timestamp = time.time()
            attempt_count = attempt_count + 1
            # TODO: The sleep time should be set based on an average time it
            # takes to process piece movements.
            time.sleep(0.02)

            # Decrease karma here to potentially block a player that
            # continually tries to move pieces when a puzzle is too active.
            if (
                len(
                    {"all", "too_active"}.intersection(
                        current_app.config["PUZZLE_RULES"]
                    )
                )
                > 0
            ) and karma > 0:
                karma = redis_connection.decr(karma_key)
                karma_change -= 1
        current_app.logger.debug(
            f"Puzzle ({puzzle}) piece move attempts: {attempt_count}"
        )
        if attempt_timestamp >= timeout:
            current_app.logger.warn(
                f"Puzzle {puzzle} is too active. Attempt piece move timed out after trying {attempt_count} times."
            )
            err_msg = {
                "msg": "Piece movement timed out.",
                "type": "error",
                "reason": "Puzzle is too active",
                "timeout": piece_move_timeout,
            }
            return make_response(
                json.jsonify(err_msg),
                503,
            )

        # Check msg for error or if piece can't be moved
        if not isinstance(msg, str):
            if isinstance(msg, dict):
                return make_response(json.jsonify(msg), 400)
            else:
                current_app.logger.warning("Unknown error: {}".format(msg))
                return make_response(
                    json.jsonify({"msg": msg, "type": "error", "timeout": 3}), 500
                )

        # publish just the bit movement so it matches what this player did
        bitmsg = formatBitMovementString(user, x, y)
        sse.publish(
            bitmsg,
            type="move",
            channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_id),
        )

        if karma_change < 0:
            if karma + recent_points <= 0:
                return _blockplayer()

        # end = time.perf_counter()
        # current_app.logger.debug("PuzzlePiecesMovePublishView {}".format(end - start))
        return make_response("", 204)


class StreamGunicornBase(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


def serve(config_file, cookie_secret):
    app = make_app(
        config=config_file, cookie_secret=cookie_secret, database_writable=False
    )
    host = app.config.get("HOSTPUBLISH")
    port = app.config.get("PORTPUBLISH")

    debug = app.config.get("DEBUG")

    app.cleanupqueue = Queue("puzzle_cleanup", connection=redis_connection)

    app.logger.info("Serving on {host}:{port}".format(**locals()))
    app.logger.info("Debug mode is {debug}".format(**locals()))

    options = {
        "loglevel": "info" if not debug else "debug",
        "timeout": 5,
        "bind": "%s:%s" % (host, port),
        "worker_class": "gevent",
        "workers": app.config.get("PUBLISH_WORKER_COUNT", number_of_workers()),
        "reload": debug,
        "preload_app": True,
        # Restart workers after this many requests just in case there are memory leaks
        "max_requests": 10000,
        "max_requests_jitter": 500,
    }
    app = StreamGunicornBase(app, options).run()


def main():
    ""
    args = docopt(__doc__, version="0.0")
    config_file = args["--config"]

    appconfig = loadConfig(config_file)
    cookie_secret = appconfig.get("SECURE_COOKIE_SECRET")

    if args["serve"]:
        serve(config_file, cookie_secret=cookie_secret)


if __name__ == "__main__":
    main()
