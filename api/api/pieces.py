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

from .constants import COMPLETED


class PuzzlePiecesView(MethodView):
    """
    Gets piece data for a puzzle.  The user is never banned from getting pieces
    and this response is cached for 10 seconds by nginx.
    """

    def get(self, puzzle_id):
        ""
        timestamp_now = int(time.time())
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

        # Load the piece data from sqlite on demand
        if not redis_connection.zscore("pcupdates", puzzle):
            # Check redis memory usage and create cleanup job if it's past a threshold
            memory = redis_connection.info(section="memory")
            current_app.logger.info("used_memory: {used_memory_human}".format(**memory))
            maxmemory = memory.get("maxmemory")
            if maxmemory != 0:
                target_memory = maxmemory * 0.5
                if memory.get("used_memory") > target_memory:
                    # push to queue for further processing
                    job = current_app.cleanupqueue.enqueue(
                        "api.jobs.convertPiecesToDB.transferOldest",
                        target_memory,
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
        publicPieceProperties = ("x", "y", "r", "s", "g", "w", "h", "b")

        # start = time.perf_counter()
        with redis_connection.pipeline(transaction=True) as pipe:
            for item in all_pieces:
                piece = item.get("id")
                pipe.hmget(
                    "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece),
                    *publicPieceProperties,
                )
            allPublicPieceProperties = pipe.execute()
        # end = time.perf_counter()
        # current_app.logger.debug("PuzzlePiecesView {}".format(end - start))

        # convert the list of lists into list of dicts.  Only want to return the public piece props.
        pieces = [
            dict(list(zip(publicPieceProperties, properties)))
            for properties in allPublicPieceProperties
        ]
        # TODO: Change piece properties to int type instead of string
        for item in all_pieces:
            piece = item.get("id")
            pieces[piece]["id"] = piece

        stamp = redis_connection.get(f"pzstamp:{puzzle}")
        if not stamp:
            stamp = uuid.uuid4().hex[:8]
        pieceData = {
            "positions": pieces,
            "timestamp": stamp,
        }

        cur.close()

        if status == COMPLETED:
            # transfer completed puzzles back out
            current_app.logger.info("transfer {0}".format(puzzle))
            job = current_app.cleanupqueue.enqueue(
                "api.jobs.convertPiecesToDB.transfer",
                puzzle,
                cleanup=True,
                skip_status_update=True,
                result_ttl=0,
            )
        else:
            # Initialize a list to temporarily store any piece movements while
            # the pieces request is cached.
            piece_cache_ttl = current_app.config.get("PUZZLE_PIECES_CACHE_TTL")
            if piece_cache_ttl:
                pcu_key = f"pcu:{stamp}"
                redis_connection.rpush(pcu_key, "")
                redis_connection.expire(pcu_key, piece_cache_ttl + 10)
                redis_connection.set(f"pzstamp:{puzzle}", stamp, ex=piece_cache_ttl)

        return make_response(json.jsonify(pieceData), 200)


class PuzzlePieceUpdatesView(MethodView):
    """"""

    def get(self, stamp):
        ""
        piece_cache_ttl = current_app.config.get("PUZZLE_PIECES_CACHE_TTL")
        if not piece_cache_ttl:
            return make_response("", 204)

        pcu_key = f"pcu:{stamp}"
        piece_updates = redis_connection.lrange(pcu_key, 0, -1)
        if len(piece_updates) == 0:
            return make_response("", 204)

        return make_response("\n".join(piece_updates), 200)


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
    """"""

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
        fetch_query_string("update_piece_props_for_puzzle.sql"),
        _piece_properties,
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
    """"""

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
        if not {
            "piece_properties",
        }.issuperset(data.keys()):
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
        if not {
            "piece_properties",
        }.issuperset(data.keys()):
            err_msg = {"msg": "Extra fields in JSON data were sent", "status_code": 400}
            return make_response(json.jsonify(err_msg), err_msg["status_code"])

        response_msg = update_puzzle_pieces(puzzle_id, data["piece_properties"])
        return make_response(json.jsonify(response_msg), response_msg["status_code"])

    def delete(self, puzzle_id):
        ""
        data = request.get_json(silent=True)
        response_msg = delete_puzzle_pieces(puzzle_id)

        return make_response(json.jsonify(response_msg), response_msg["status_code"])
