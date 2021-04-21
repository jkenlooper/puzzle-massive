from __future__ import absolute_import
from builtins import zip
from flask import abort, json, make_response
from flask.views import MethodView

from .app import db, redis_connection
from .database import fetch_query_string, rowify
from .user import user_not_banned

encoder = json.JSONEncoder(indent=2, sort_keys=True)


class PuzzlePieceView(MethodView):
    """
    Get info about a single puzzle piece.
    """

    decorators = [user_not_banned]

    def get(self, puzzle_id, piece):

        cur = db.cursor()
        result = cur.execute(
            fetch_query_string("select_puzzle_id_by_puzzle_id.sql"),
            {"puzzle_id": puzzle_id},
        ).fetchall()
        if not result:
            # 404 if puzzle or piece does not exist
            cur.close()
            db.commit()
            abort(404)

        (result, col_names) = rowify(result, cur.description)
        puzzle = result[0].get("puzzle")
        cur.close()

        # Only allow if there is data in redis
        if not redis_connection.zscore("pcupdates", puzzle):
            abort(400)

        # Fetch just the piece properties
        # The 'rotate' field is not public. It is for the true orientation of the piece.
        # The 'r' field is the mutable rotation of the piece.
        publicPieceProperties = ("x", "y", "r", "s", "g", "w", "h", "b")
        pieceProperties = redis_connection.hmget(
            "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece),
            *publicPieceProperties
        )
        pieceData = dict(list(zip(publicPieceProperties, pieceProperties)))
        pieceData["id"] = piece
        return make_response(json.jsonify(pieceData), 200)
