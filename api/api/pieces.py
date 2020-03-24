from __future__ import print_function
from __future__ import absolute_import
from builtins import zip
import time
import uuid

from flask import current_app, make_response, request, abort, json

from flask.views import MethodView
from werkzeug.exceptions import HTTPException

from .app import db, redis_connection
from .database import fetch_query_string, rowify
from .tools import formatPieceMovementString
from .jobs.convertPiecesToRedis import convert
from .user import user_id_from_ip, increase_ban_time

from .constants import COMPLETED

# from jobs import pieceMove

encoder = json.JSONEncoder(indent=2, sort_keys=True)

# TODO: create a puzzle status web socket that will update when the status of
# the puzzle changes from converting, done, active, etc.

# How many puzzles a user can open within this many seconds before being banned.
# Allow 10 puzzles to be open within 100 seconds.
PUZZLE_VIEW_RATE_TIMEOUT = 100
PUZZLE_VIEW_MAX_COUNT = 10
BAN_TIME_INCR_FOR_EACH = 60 * 5


class PuzzlePiecesView(MethodView):
    """
    Gets piece data for a puzzle.  The user is never banned from getting pieces,
    but loading pieces too often can get the user on the banned list.
    """

    def bump_count(self, user):
        """
        Bump the count for puzzle loaded for this user.
        Note that this is different when a player moves a piece on a puzzle
        that they just opened. The recent points in karma just prevents abuse
        from humans.
        """
        timestamp_now = int(time.time())
        rounded_timestamp = timestamp_now - (timestamp_now % PUZZLE_VIEW_RATE_TIMEOUT)

        # TODO: optimize the timestamp used here by truncating to last digits based
        # on the expiration of the key.
        puzzle_view_rate_key = "pvrate:{user}:{timestamp}".format(
            user=user, timestamp=rounded_timestamp
        )
        if redis_connection.setnx(puzzle_view_rate_key, 1):
            redis_connection.expire(puzzle_view_rate_key, PUZZLE_VIEW_RATE_TIMEOUT)
        else:
            count = redis_connection.incr(puzzle_view_rate_key)
            if count > PUZZLE_VIEW_MAX_COUNT:
                increase_ban_time(user, BAN_TIME_INCR_FOR_EACH)

    def get(self, puzzle_id):
        ""
        ip = request.headers.get("X-Real-IP")
        user = int(current_app.secure_cookie.get(u"user") or user_id_from_ip(ip))
        self.bump_count(user)

        cur = db.cursor()
        result = cur.execute(
            fetch_query_string("select_viewable_puzzle_id.sql"),
            {"puzzle_id": puzzle_id},
        ).fetchall()
        if not result:
            # 404 if puzzle or piece does not exist
            cur.close()
            db.commit()
            abort(404)

        (result, col_names) = rowify(result, cur.description)
        puzzle = result[0].get("puzzle")
        status = result[0].get("status")

        # TODO: if puzzle is not in redis then create a job to convert and respond with a 202 Accepted
        # if job is already active for this request respond with 202 Accepted

        # Load the piece data from sqlite on demand
        if not redis_connection.zscore("pcupdates", puzzle):
            # if not redis_connection.exists('pc:{puzzle}:0'.format(puzzle=puzzle)):
            # TODO: publish the job to the worker queue
            # Respond with 202

            # Check redis memory usage and create cleanup job if it's past a threshold
            memory = redis_connection.info(section="memory")
            print("used_memory: {used_memory_human}".format(**memory))
            maxmemory = memory.get("maxmemory")
            if maxmemory != 0:
                target_memory = maxmemory * 0.5
                if memory.get("used_memory") > target_memory:
                    # push to queue for further processing
                    job = current_app.cleanupqueue.enqueue_call(
                        func="api.jobs.convertPiecesToDB.transferOldest",
                        args=(target_memory,),
                        result_ttl=0,
                    )

            # For now just convert as it doesn't take long
            convert(puzzle)

        (all_pieces, col_names) = rowify(
            cur.execute(
                fetch_query_string("select_all_piece_ids_for_puzzle.sql"),
                {"puzzle": puzzle},
            ).fetchall(),
            cur.description,
        )

        # Create a pipe for buffering commands and disable atomic transactions
        pipe = redis_connection.pipeline(transaction=False)

        # The 'rotate' field is not public. It is for the true orientation of the piece.
        # The 'r' field is the mutable rotation of the piece.
        publicPieceProperties = ("x", "y", "r", "s", "w", "h", "b")

        for item in all_pieces:
            piece = item.get("id")
            pipe.hmget(
                "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece),
                *publicPieceProperties
            )
        allPublicPieceProperties = pipe.execute()
        # convert the list of lists into list of dicts.  Only want to return the public piece props.
        pieces = [
            dict(list(zip(publicPieceProperties, properties)))
            for properties in allPublicPieceProperties
        ]
        # TODO: Change piece properties to int type instead of string
        for item in all_pieces:
            piece = item.get("id")
            pieces[piece]["id"] = piece

        pieceData = {
            "positions": pieces,
            "timestamp": "",
            "mark": uuid.uuid4().hex[
                :3
            ],  # Used to differentiate any requests for a user session (handle double-clicking pieces)
        }

        cur.close()

        if status == COMPLETED:
            # transfer completed puzzles back out
            print("transfer {0}".format(puzzle))
            job = current_app.cleanupqueue.enqueue_call(
                func="api.jobs.convertPiecesToDB.transfer", args=(puzzle,), result_ttl=0
            )

        return encoder.encode(pieceData)
        # TODO: update js code to properly handle json mimetype
        # return make_response(json.jsonify(pieceData), 200)
