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

encoder = json.JSONEncoder(indent=2, sort_keys=True)

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
            current_app.logger.info("used_memory: {used_memory_human}".format(**memory))
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

        # The 'rotate' field is not public. It is for the true orientation of the piece.
        # The 'r' field is the mutable rotation of the piece.
        publicPieceProperties = ("x", "y", "r", "s", "w", "h", "b")

        with redis_connection.pipeline(transaction=True) as pipe:
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
            current_app.logger.info("transfer {0}".format(puzzle))
            job = current_app.cleanupqueue.enqueue_call(
                func="api.jobs.convertPiecesToDB.transfer",
                args=(puzzle,),
                kwargs={"cleanup": True},
                result_ttl=0,
            )

        return encoder.encode(pieceData)
        # TODO: update js code to properly handle json mimetype
        # return make_response(json.jsonify(pieceData), 200)


immutable_attrs = {
    "id",
    "puzzle",
}
mutable_attrs = {
    "adjacent",
    "b",
    "col",
    "h",
    "parent",
    "r",
    "rotate",
    "row",
    "status",
    "w",
    "x",
    "y",
}
# piece_attrs should match queries/select_all_piece_props_for_puzzle.sql
piece_attrs = immutable_attrs.union(mutable_attrs)


def update_puzzle_pieces(puzzle_id, piece_properties):
    """
    """

    if not isinstance(piece_properties, list):
        err_msg = {"msg": "piece_properties should be list", "status_code": 400}
        return err_msg
    # validate each piece property
    for piece in piece_properties:
        if not piece_attrs.issuperset(piece.keys()):
            err_msg = {"msg": "has extra piece property", "status_code": 400}
            return err_msg

    cur = db.cursor()
    result = cur.execute(
        fetch_query_string("select-internal-puzzle-details-for-puzzle_id.sql"),
        {"puzzle_id": puzzle_id},
    ).fetchall()
    if not result:
        err_msg = {"msg": "No puzzle found", "status_code": 400}
        cur.close()
        return err_msg

    (result, col_names) = rowify(result, cur.description)
    puzzle_data = result[0]
    puzzle = puzzle_data["id"]

    # get all current piece props
    result = cur.execute(
        fetch_query_string("select_all_piece_props_for_puzzle.sql"), {"puzzle": puzzle}
    ).fetchall()
    if not result:
        err_msg = {"msg": "No pieces found for puzzle", "status_code": 400}
        cur.close()
        return err_msg
    (result, col_names) = rowify(result, cur.description)
    current_piece_properties = {x["id"]: x for x in result}

    def set_attrs(piece):
        _piece = current_piece_properties[piece["id"]]
        _piece.update(piece)
        return _piece

    def is_different(piece):
        return piece != current_piece_properties[piece["id"]]

    # filter out any pieces that are same as current
    # update current piece props
    _piece_properties = list(map(set_attrs, filter(is_different, piece_properties)))

    cur.executemany(
        fetch_query_string("update_piece_props_for_puzzle.sql"), _piece_properties,
    )
    db.commit()
    cur.close()

    msg = {
        "rowcount": len(_piece_properties),
        "msg": "Updated",
        "status_code": 200,
    }
    return msg


def add_puzzle_pieces(puzzle_id, piece_properties):
    """
    piece_properties is a list of piece properties
    """

    if not isinstance(piece_properties, list):
        err_msg = {"msg": "piece_properties should be list", "status_code": 400}
        return err_msg
    # validate each piece property
    for piece in piece_properties:
        if not piece_attrs == piece.keys():
            err_msg = {"msg": "has extra piece property", "status_code": 400}
            return err_msg

    cur = db.cursor()
    result = cur.execute(
        fetch_query_string("select-internal-puzzle-details-for-puzzle_id.sql"),
        {"puzzle_id": puzzle_id},
    ).fetchall()
    if not result:
        err_msg = {"msg": "No puzzle found", "status_code": 400}
        cur.close()
        return err_msg

    (result, col_names) = rowify(result, cur.description)
    puzzle_data = result[0]
    puzzle = puzzle_data["id"]

    cur.executemany(
        """
        insert or ignore into Piece (id, x, y, r, w, h, b, adjacent, rotate, row, col, status, parent, puzzle) values (
      :id, :x, :y, :r, :w, :h, :b, :adjacent, :rotate, :row, :col, :status, :parent, :puzzle
        );""",
        piece_properties,
    )
    db.commit()

    cur.close()

    msg = {"rowcount": len(piece_properties), "msg": "Inserted", "status_code": 200}
    return msg


def delete_puzzle_pieces(puzzle_id):
    """
    """

    cur = db.cursor()
    result = cur.execute(
        fetch_query_string("select-internal-puzzle-details-for-puzzle_id.sql"),
        {"puzzle_id": puzzle_id},
    ).fetchall()
    if not result:
        err_msg = {"msg": "No puzzle found", "status_code": 400}
        cur.close()
        return err_msg

    (result, col_names) = rowify(result, cur.description)
    puzzle_data = result[0]
    puzzle = puzzle_data["id"]

    result = cur.execute("delete from Piece where puzzle = :puzzle", {"puzzle": puzzle})
    db.commit()
    cur.close()

    msg = {"rowcount": result.rowcount, "msg": "Deleted", "status_code": 200}
    return msg


class InternalPuzzlePiecesView(MethodView):
    """
    Internal puzzle pieces view for use by other apps. Allows modifying piece data.
    """

    def post(self, puzzle_id):
        ""
        data = request.get_json(silent=True)
        if not data:
            err_msg = {"msg": "No JSON data sent", "status_code": 400}
            return make_response(json.jsonify(err_msg), err_msg["status_code"])
        if not {"piece_properties",}.issuperset(data.keys()):
            err_msg = {"msg": "Extra fields in JSON data were sent", "status_code": 400}
            return make_response(json.jsonify(err_msg), err_msg["status_code"])
        response_msg = add_puzzle_pieces(puzzle_id, data["piece_properties"])

        return make_response(json.jsonify(response_msg), response_msg["status_code"])

    def patch(self, puzzle_id):
        ""
        data = request.get_json(silent=True)

        if not data:
            err_msg = {"msg": "No JSON data sent", "status_code": 400}
            return make_response(json.jsonify(err_msg), err_msg["status_code"])
        if not {"piece_properties",}.issuperset(data.keys()):
            err_msg = {"msg": "Extra fields in JSON data were sent", "status_code": 400}
            return make_response(json.jsonify(err_msg), err_msg["status_code"])

        response_msg = update_puzzle_pieces(puzzle_id, data["piece_properties"])
        return make_response(json.jsonify(response_msg), response_msg["status_code"])

    def delete(self, puzzle_id):
        ""
        # api/api/jobs/pieceRenderer.py render
        # internal-puzzle-pieces "delete from Piece where puzzle = :puzzle"
        data = request.get_json(silent=True)
        response_msg = delete_puzzle_pieces(puzzle_id)

        return make_response(json.jsonify(response_msg), response_msg["status_code"])
