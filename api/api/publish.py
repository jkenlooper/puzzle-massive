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
from past.utils import old_div
import datetime
import sys
import time
import random
import uuid
from subprocess import Popen
import multiprocessing
from docopt import docopt
import os

import gunicorn.app.base
from flask import current_app, make_response, request, json, url_for, redirect, Flask, g
from flask.views import MethodView
from werkzeug.exceptions import HTTPException
from flask_sse import sse
from redis.exceptions import WatchError
from rq import Worker, Queue

from api.flask_secure_cookie import SecureCookie
from api.app import db, redis_connection
from api.database import fetch_query_string, rowify
from api.tools import (
    loadConfig,
    formatPieceMovementString,
    formatBitMovementString,
    init_karma_key,
    get_public_karma_points,
    files_loader,
)

from api.constants import (
    ACTIVE,
    BUGGY_UNLISTED,
)

# from jobs import pieceMove
from api.jobs import pieceTranslate
from api.piece_mutate import PieceMutateError
from api.user import user_id_from_ip, user_not_banned, increase_ban_time

encoder = json.JSONEncoder(indent=2, sort_keys=True)

HOUR = 3600  # hour in seconds
MINUTE = 60  # minute in seconds

BLOCKEDPLAYER_EXPIRE_TIMEOUT = HOUR
MAX_KARMA = 25
MIN_KARMA = int(old_div(MAX_KARMA, 2)) * -1  # -12
MOVES_BEFORE_PENALTY = 12
STACK_PENALTY = 1
HOTSPOT_EXPIRE = 30
HOTSPOT_LIMIT = 10
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

TOKEN_EXPIRE_TIMEOUT = 60 * 5
TOKEN_LOCK_TIMEOUT = 5
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

    @app.teardown_appcontext
    def teardown_db(exception):
        db = getattr(g, "_database", None)
        if db is not None:
            db.close()

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
    The nginx conf has a 60r/m with a burst of 60 on this route. The goal here
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


class PuzzlePieceTokenView(MethodView):
    """
    player gets token after mousedown.  /puzzle/<puzzle_id>/piece/<int:piece>/token/
    """

    decorators = [user_not_banned]

    def get(self, puzzle_id, piece):
        ip = request.headers.get("X-Real-IP")
        user = current_app.secure_cookie.get(u"user") or user_id_from_ip(ip)
        if user == None:
            err_msg = {
                "msg": "Please reload the page.",
                "reason": "The player login that you were using is no longer valid.  This may have happened if another player on your network has selected a bit icon.  Refreshing the page should set a new player login cookie.",
                "type": "puzzlereload",
                "timeout": 300,
            }
            response = make_response(encoder.encode(err_msg), 400)
            expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
            current_app.secure_cookie.set(u"user", "", response, expires=expires)
            current_app.secure_cookie.set(u"shareduser", "", response, expires=expires)
            return response

        user = int(user)
        mark = request.args.get("mark", "000")[:3]
        now = int(time.time())

        pzq_key = "pzq:{puzzle_id}".format(puzzle_id=puzzle_id)
        puzzle = redis_connection.hget(pzq_key, "puzzle")
        if not puzzle:
            # Start db operations
            cur = db.cursor()
            # validate the puzzle_id
            result = cur.execute(
                fetch_query_string("select_puzzle_and_piece.sql"),
                {"puzzle_id": puzzle_id},
            ).fetchall()
            if not result:
                # 400 if puzzle does not exist or piece is not found
                # Only puzzles in ACTIVE state can be mutated
                err_msg = {
                    "msg": "puzzle is not ready at this time. Please reload the page.",
                    "type": "puzzleimmutable",
                }
                cur.close()
                return make_response(encoder.encode(err_msg), 400)
            (result, col_names) = rowify(result, cur.description)
            cur.close()
            puzzle_data = result[0]
            puzzle = puzzle_data["puzzle"]

        (piece_status, has_y) = redis_connection.hmget(
            "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece), ["s", "y"]
        )

        if has_y == None:
            # 400 if puzzle does not exist or piece is not found
            # Only puzzles in ACTIVE state can be mutated
            err_msg = {
                "msg": "puzzle pieces can't be moved at this time. Please reload the page.",
                "type": "puzzleimmutable",
            }
            return make_response(encoder.encode(err_msg), 400)

        if piece_status == "1":
            # immovable
            err_msg = {
                "msg": "piece can't be moved",
                "type": "immovable",
                "expires": now + 5,
                "timeout": 5,
            }
            return make_response(encoder.encode(err_msg), 400)

        blockedplayers_for_puzzle_key = "blockedplayers:{puzzle}".format(puzzle=puzzle)
        blockedplayers_expires = redis_connection.zscore(
            blockedplayers_for_puzzle_key, user
        )
        if blockedplayers_expires and blockedplayers_expires > now:
            err_msg = get_blockedplayers_err_msg(
                blockedplayers_expires, blockedplayers_expires - now
            )
            return make_response(encoder.encode(err_msg), 429)

        puzzle_piece_token_key = get_puzzle_piece_token_key(puzzle, piece)

        # Check if player already has a token for this puzzle. This would mean
        # that the player tried moving another piece before the locked piece
        # finished moving.
        existing_token = redis_connection.get("token:{}".format(user))
        if existing_token:
            (player_puzzle, player_piece, player_mark) = existing_token.split(":")
            player_puzzle = int(player_puzzle)
            player_piece = int(player_piece)
            if player_puzzle == puzzle:
                # Temporary ban the player when clicking a piece and not
                # dropping it before clicking another piece.
                if player_mark == mark:
                    # Ban the user for a few seconds
                    err_msg = increase_ban_time(user, TOKEN_LOCK_TIMEOUT)
                    err_msg[
                        "reason"
                    ] = "Concurrent piece movements on this puzzle from the same player are not allowed."
                    return make_response(encoder.encode(err_msg), 429)

                else:
                    # Block the player from selecting pieces on this puzzle
                    err_msg = {
                        "msg": "Please wait or do a different puzzle. New players on the same network will be sharing the same bit icon.  Please register as a separate player once enough dots are earned to select a new bit icon.",
                        "type": "sameplayerconcurrent",
                        "reason": "Concurrent piece movements on this puzzle from the same player are not allowed.",
                        "expires": now + TOKEN_LOCK_TIMEOUT,
                        "timeout": TOKEN_LOCK_TIMEOUT,
                    }

                    uses_cookies = current_app.secure_cookie.get(u"ot")
                    if uses_cookies:
                        # Check if player has enough dots to generate a new
                        # player and if so add to err_msg to signal client to
                        # request a new player
                        cur = db.cursor()
                        dots = cur.execute(
                            "select points from User where id = :id and points >= :cost + :startpoints;",
                            {
                                "id": user,
                                "cost": current_app.config[
                                    "POINT_COST_FOR_CHANGING_BIT"
                                ],
                                "startpoints": current_app.config[
                                    "NEW_USER_STARTING_POINTS"
                                ],
                            },
                        ).fetchone()
                        if result:
                            err_msg["action"] = {
                                "msg": "Create a new player?",
                                "url": "/newapi{}".format(url_for("split-player")),
                            }
                        cur.close()
                    return make_response(encoder.encode(err_msg), 409)

        piece_token_queue_key = get_puzzle_piece_token_queue_key(puzzle, piece)
        queue_rank = redis_connection.zrank(piece_token_queue_key, user)

        if queue_rank == None:
            # Append this player to a queue for getting the next token. This
            # will prevent the player with the lock from continually locking the
            # same piece.
            redis_connection.zadd(piece_token_queue_key, {user: now})
            queue_rank = redis_connection.zrank(piece_token_queue_key, user)
        redis_connection.expire(piece_token_queue_key, TOKEN_LOCK_TIMEOUT + 5)

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
            return make_response(encoder.encode(err_msg), 409)

        # Check if token on piece is still owned by another player
        existing_token_and_player = redis_connection.get(puzzle_piece_token_key)
        if existing_token_and_player:
            (other_token, other_player) = existing_token_and_player.split(":")
            other_player = int(other_player)
            puzzle_and_piece = redis_connection.get("token:{}".format(other_player))
            # Check if there is a lock on this piece by other player
            if puzzle_and_piece:
                (other_puzzle, other_piece, other_mark) = puzzle_and_piece.split(":")
                other_puzzle = int(other_puzzle)
                other_piece = int(other_piece)
                if (
                    other_puzzle == puzzle
                    and other_piece == piece
                    and other_player != user
                ):
                    # Other player has a lock on this piece
                    err_msg = {
                        "msg": "Another player is moving this piece",
                        "type": "piecelock",
                        "reason": "Piece locked",
                        "expires": now + TOKEN_LOCK_TIMEOUT,
                        "timeout": TOKEN_LOCK_TIMEOUT,
                    }
                    return make_response(encoder.encode(err_msg), 409)

        # Remove player from the piece token queue
        redis_connection.zrem(piece_token_queue_key, user)

        # This piece is up for grabs since it has been more then 5 seconds since
        # another player has grabbed it.
        token = uuid.uuid4().hex
        redis_connection.set(
            puzzle_piece_token_key,
            "{token}:{user}".format(token=token, user=user),
            ex=TOKEN_EXPIRE_TIMEOUT,
        )
        redis_connection.set(
            "token:{}".format(user),
            "{puzzle}:{piece}:{mark}".format(puzzle=puzzle, piece=piece, mark=mark),
            ex=TOKEN_LOCK_TIMEOUT,
        )

        # Claim the piece by showing the bit icon next to it.
        (x, y) = list(
            map(
                int,
                redis_connection.hmget(
                    "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece), ["x", "y"]
                ),
            )
        )
        msg = formatBitMovementString(user, x, y)

        sse.publish(
            msg, type="move", channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_id)
        )

        response = {
            "token": token,
            "lock": now + TOKEN_LOCK_TIMEOUT,
            "expires": now + TOKEN_EXPIRE_TIMEOUT,
        }
        return encoder.encode(response)


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

    Return karma amount
    """

    decorators = [user_not_banned]
    ACCEPTABLE_ARGS = set(["x", "y", "r"])

    def patch(self, puzzle_id, piece):
        """
        args:
        x
        y
        r
        """
        ip = request.headers.get("X-Real-IP")
        user = int(current_app.secure_cookie.get(u"user") or user_id_from_ip(ip))
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
            return make_response(encoder.encode(err_msg), 400)
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
            return make_response(encoder.encode(err_msg), 400)
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
                    return make_response(encoder.encode(err_msg), 400)
        x = args.get("x")
        y = args.get("y")
        r = args.get("r")

        timestamp_now = int(time.time())

        pzq_key = "pzq:{puzzle_id}".format(puzzle_id=puzzle_id)
        pzq_fields = [
            "puzzle",
            "table_width",
            "table_height",
            "permission",
            "pieces",
            "q",
        ]
        puzzle_data = dict(zip(pzq_fields, redis_connection.hmget(pzq_key, pzq_fields)))
        puzzle = puzzle_data.get("puzzle")
        if puzzle == None:
            # Start db operations
            cur = db.cursor()
            # validate the puzzle_id
            result = cur.execute(
                fetch_query_string("select_puzzle_and_piece.sql"),
                {"puzzle_id": puzzle_id},
            ).fetchall()
            if not result:
                err_msg = {"msg": "puzzle not available", "type": "missing"}
                cur.close()
                return make_response(encoder.encode(err_msg), 404)
            (result, col_names) = rowify(result, cur.description)
            cur.close()
            puzzle_data = result[0]
            redis_connection.hmset(
                pzq_key,
                {
                    "puzzle": puzzle_data["puzzle"],
                    "table_width": puzzle_data["table_width"],
                    "table_height": puzzle_data["table_height"],
                    "permission": puzzle_data["permission"],
                    "pieces": puzzle_data["pieces"],
                    # "q": "", # q is set later
                },
            )
            redis_connection.expire(pzq_key, 300)
        else:
            puzzle_data["puzzle"] = int(puzzle_data["puzzle"])
            puzzle_data["table_width"] = int(puzzle_data["table_width"])
            puzzle_data["table_height"] = int(puzzle_data["table_height"])
            puzzle_data["permission"] = int(puzzle_data["permission"])
            puzzle_data["pieces"] = int(puzzle_data["pieces"])
        puzzle = puzzle_data["puzzle"]
        puzzle_data["puzzle_id"] = puzzle_id

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
            return make_response(encoder.encode(err_msg), 400)
        puzzle_piece_token_key = get_puzzle_piece_token_key(puzzle, piece)
        # print("token key: {}".format(puzzle_piece_token_key))
        token_and_player = redis_connection.get(puzzle_piece_token_key)
        if token_and_player:
            player = user
            (valid_token, other_player) = token_and_player.split(":")
            other_player = int(other_player)
            if token != valid_token:
                # print("token invalid {} != {}".format(token, valid_token))
                err_msg = increase_ban_time(user, TOKEN_INVALID_BAN_TIME_INCR)
                err_msg["reason"] = "Token is invalid"
                return make_response(encoder.encode(err_msg), 409)
            if player != other_player:
                # print("player invalid {} != {}".format(player, other_player))
                err_msg = increase_ban_time(user, TOKEN_INVALID_BAN_TIME_INCR)
                err_msg["reason"] = "Player is invalid"
                return make_response(encoder.encode(err_msg), 409)
        else:
            # Token has expired
            # print("token expired")
            err_msg = {"msg": "Token has expired", "type": "expiredtoken", "reason": ""}
            return make_response(encoder.encode(err_msg), 409)

        # Expire the token at the lock timeout since it shouldn't be used again
        redis_connection.delete(puzzle_piece_token_key)
        redis_connection.delete("token:{}".format(user))

        err_msg = bump_count(user)
        if err_msg.get("type") == "bannedusers":
            return make_response(encoder.encode(err_msg), 429)

        # TODO: has this moved elsewhere?
        ## check if piece can be moved
        # (piece_status, has_y) = redis_connection.hmget(
        #    "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece),
        #    ["s", "y"],
        # )
        # if has_y == None:
        #    err_msg = {"msg": "piece not available", "type": "missing"}
        #    return make_response(encoder.encode(err_msg), 404)

        # if piece_status == "1":
        #    # immovable
        #    err_msg = {
        #        "msg": "piece can't be moved",
        #        "type": "immovable",
        #        "expires": now + 5,
        #        "timeout": 5,
        #    }
        #    return make_response(encoder.encode(err_msg), 400)

        # check if piece will be moved to within boundaries
        if x and (x < 0 or x > puzzle_data["table_width"]):
            err_msg = {
                "msg": "Piece movement out of bounds",
                "type": "invalidpiecemove",
                "expires": now + 5,
                "timeout": 5,
            }
            return make_response(encoder.encode(err_msg), 400)
        if y and (y < 0 or y > puzzle_data["table_height"]):
            err_msg = {
                "msg": "Piece movement out of bounds",
                "type": "invalidpiecemove",
                "expires": now + 5,
                "timeout": 5,
            }
            return make_response(encoder.encode(err_msg), 400)

        # Set the rounded timestamp
        rounded_timestamp = timestamp_now - (
            timestamp_now % PIECE_MOVEMENT_RATE_TIMEOUT
        )

        # Update karma
        karma_key = init_karma_key(redis_connection, puzzle, ip)
        # Set a limit to minimum karma so other players on the network can still play
        karma = max(MIN_KARMA, int(redis_connection.get(karma_key)))
        # initial_karma = max(0, min(100/2, karma))
        karma_change = 0

        points_key = "points:{user}".format(user=user)

        # Decrease recent points if this is a new puzzle that user hasn't moved pieces on yet in the last hour
        pzrate_key = "pzrate:{user}:{today}".format(
            user=user, today=datetime.date.today().isoformat()
        )
        if redis_connection.sadd(pzrate_key, puzzle) == 1:
            # New puzzle that player hasn't moved a piece on in the last hour.
            redis_connection.expire(pzrate_key, HOUR)
            recent_points = int(redis_connection.get(points_key) or "0")
            if recent_points > 0:
                redis_connection.decr(points_key)

        # Decrease karma if piece movement rate has passed threshold
        # TODO: remove timestamp from key and depend on expire setting
        pcrate_key = "pcrate:{puzzle}:{user}:{timestamp}".format(
            puzzle=puzzle, user=user, timestamp=rounded_timestamp
        )
        if redis_connection.setnx(pcrate_key, 1):
            redis_connection.expire(pcrate_key, PIECE_MOVEMENT_RATE_TIMEOUT)
        else:
            moves = redis_connection.incr(pcrate_key)
            if moves > PIECE_MOVEMENT_RATE_LIMIT:
                # print 'decrease because piece movement rate limit reached.'
                if karma > MIN_KARMA:
                    karma = redis_connection.decr(karma_key)
                karma_change -= 1

        # Decrease karma when moving the same piece again within a minute
        # TODO: remove timestamp from key and depend on expire setting
        hotpc_key = "hotpc:{puzzle}:{user}:{piece}:{timestamp}".format(
            puzzle=puzzle, user=user, piece=piece, timestamp=rounded_timestamp
        )
        recent_move_count = redis_connection.incr(hotpc_key)
        if recent_move_count == 1:
            redis_connection.expire(hotpc_key, PIECE_MOVEMENT_RATE_TIMEOUT)

        if recent_move_count > MOVES_BEFORE_PENALTY:
            if karma > MIN_KARMA:
                karma = redis_connection.decr(karma_key)
            karma_change -= 1

        if int(karma) <= 0:
            # Decrease recent points for a piece move that decreased karma
            recent_points = (
                redis_connection.decr(points_key, amount=abs(karma_change))
                if karma_change < 0
                else int(redis_connection.get(points_key) or 0)
            )
            redis_connection.set(points_key, max(0, recent_points))
            if int(karma) + recent_points <= 0:
                expires = now + BLOCKEDPLAYER_EXPIRE_TIMEOUT
                blockedplayers_for_puzzle_key = "blockedplayers:{puzzle}".format(
                    puzzle=puzzle
                )
                # Add the player to the blocked players list for the puzzle and
                # extend the expiration of the key.
                redis_connection.zadd(blockedplayers_for_puzzle_key, {user: expires})
                redis_connection.expire(
                    blockedplayers_for_puzzle_key, BLOCKEDPLAYER_EXPIRE_TIMEOUT
                )

                # Reset the karma for the player
                redis_connection.delete(karma_key)

                # TODO: drop these keys
                redis_connection.zadd(
                    "blockedplayers",
                    {"{ip}-{user}".format(ip=ip, user=user): int(time.time())},
                )
                redis_connection.zadd(
                    "blockedplayers:puzzle",
                    {
                        "{ip}-{user}-{puzzle}".format(
                            ip=ip, user=user, puzzle=puzzle
                        ): int(recent_points)
                    },
                )

                err_msg = get_blockedplayers_err_msg(expires, expires - now)
                err_msg["karma"] = get_public_karma_points(
                    redis_connection, ip, user, puzzle
                )
                return make_response(encoder.encode(err_msg), 429)

        if puzzle_data.get("q") == None or not redis_connection.sismember(
            "pzq_register", puzzle_data.get("q")
        ):
            # Assign this puzzle to a piece translate worker queue with the
            # least amount of activity.
            queue_names = list(redis_connection.smembers("pzq_register"))
            if len(queue_names) == 0:
                current_app.logger.error(
                    "No workers found for piece translate queues (pzq_register)"
                )
                return make_response(
                    encoder.encode(
                        {
                            "msg": "Server error",
                            "type": "error",
                            "reason": "No workers",
                            "expires": now + 5,
                            "timeout": 5,
                        }
                    ),
                    500,
                )
            queue_name = queue_names[0]
            with redis_connection.pipeline(transaction=True) as pipe:
                for qn in queue_names:
                    pipe.zcount(
                        "pzq_activity:{queue_name}".format(queue_name=qn),
                        timestamp_now - 300,
                        timestamp_now,
                    )
                least_active_queue = None
                count = None
                for (qn, activity_count) in zip(queue_names, pipe.execute()):
                    if count is None or activity_count < count:
                        queue_name = qn
                        count = activity_count

            redis_connection.hset(pzq_key, "q", queue_name)
            puzzle_data["q"] = queue_name

        # TODO: move this to pieceTranslate
        # Check if there are too many pieces stacked. Slightly less exact from
        # what pieceTranslate does.  This includes immovable pieces, and the
        # pieces own group which would normally be filtered out when checking
        # if the piece can be joined.
        (pieceWidth, pieceHeight) = list(
            map(
                int,
                redis_connection.hmget(
                    "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece), ["w", "h"]
                ),
            )
        )
        toleranceX = min(pieceWidth, 200)
        toleranceY = min(pieceHeight, 200)
        proximityX = set(
            map(
                int,
                redis_connection.zrangebyscore(
                    "pcx:{puzzle}".format(puzzle=puzzle),
                    x - toleranceX,
                    x + toleranceX,
                ),
            )
        )
        proximityY = set(
            map(
                int,
                redis_connection.zrangebyscore(
                    "pcy:{puzzle}".format(puzzle=puzzle),
                    y - toleranceY,
                    y + toleranceY,
                ),
            )
        )
        piecesInProximity = set.intersection(proximityX, proximityY)
        if len(piecesInProximity) >= 13:
            if karma > MIN_KARMA:
                karma = redis_connection.decr(karma_key, amount=STACK_PENALTY)
            err_msg = get_too_many_pieces_in_proximity_err_msg(
                piece, list(piecesInProximity)
            )
            err_msg["karma"] = get_public_karma_points(
                redis_connection, ip, user, puzzle
            )
            # TODO: should publish a message so only the user will get the message
            return make_response(encoder.encode(err_msg), 400)

        # Record hot spot (not exact)
        # TODO: remove timestamp from key and rely on expire setting
        rounded_timestamp_hotspot = timestamp_now - (timestamp_now % HOTSPOT_EXPIRE)
        hotspot_area_key = "hotspot:{puzzle}:{user}:{timestamp}:{x}:{y}".format(
            puzzle=puzzle,
            user=user,
            timestamp=rounded_timestamp_hotspot,
            x=x - (x % 200),
            y=y - (y % 200),
        )
        hotspot_count = redis_connection.incr(hotspot_area_key)
        if hotspot_count == 1:
            redis_connection.expire(hotspot_area_key, HOTSPOT_EXPIRE)
        if hotspot_count > HOTSPOT_LIMIT:
            if karma > MIN_KARMA:
                karma = redis_connection.decr(karma_key)
            karma_change -= 1

        pz_translate_queue = Queue(puzzle_data.get("q"), connection=redis_connection)

        # Push to queue for further processing by a single worker.
        # Record timestamp of queue activity

        redis_connection.zadd(
            "pzq_activity:{queue_name}".format(queue_name=puzzle_data["q"]),
            {timestamp_now: timestamp_now},
        )
        job = pz_translate_queue.enqueue_call(
            func="api.jobs.pieceTranslate.attempt_piece_movement",
            args=(ip, user, puzzle_data, piece, x, y, r, karma_change,),
            result_ttl=0,
            timeout=10,
            ttl=None,
        )

        # publish just the bit movement so it matches what this player did
        msg = formatBitMovementString(user, x, y)
        sse.publish(
            msg, type="move", channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_id)
        )

        karma_change = False if karma_change == 0 else karma_change

        karma = get_public_karma_points(redis_connection, ip, user, puzzle)
        response = {"karma": karma, "karmaChange": karma_change, "id": piece}
        return encoder.encode(response)


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

    app.logger.info(u"Serving on {host}:{port}".format(**locals()))
    app.logger.info(u"Debug mode is {debug}".format(**locals()))

    options = {
        "loglevel": "info" if not debug else "debug",
        "timeout": 5,
        "bind": "%s:%s" % (host, port),
        "worker_class": "gevent",
        "workers": number_of_workers(),
        "reload": debug,
        "preload_app": True,
        # Restart workers after this many requests just in case there are memory leaks
        "max_requests": 1000,
        "max_requests_jitter": 50,
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
