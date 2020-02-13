from __future__ import absolute_import
from builtins import zip
from flask import abort, json, current_app, request, make_response
from flask.views import MethodView

from .app import db, redis_connection
from .database import fetch_query_string, rowify
from .user import user_not_banned, user_id_from_ip

encoder = json.JSONEncoder(indent=2, sort_keys=True)


class PuzzlePieceView(MethodView):
    """
    Get info about a single puzzle piece.
    """

    decorators = [user_not_banned]

    def get(self, puzzle_id, piece):

        ip = request.headers.get("X-Real-IP")
        user = int(current_app.secure_cookie.get(u"user") or user_id_from_ip(ip))
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
        db.commit()

        # Only allow if there is data in redis
        if not redis_connection.zscore("pcupdates", puzzle):
            abort(400)

        # Expire the token at the lock timeout since it shouldn't be used again
        redis_connection.delete(
            "pctoken:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece)
        )
        redis_connection.delete("token:{}".format(user))

        # Fetch just the piece properties
        publicPieceProperties = ("x", "y", "rotate", "s", "w", "h", "b")
        pieceProperties = redis_connection.hmget(
            "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece),
            *publicPieceProperties
        )
        pieceData = dict(list(zip(publicPieceProperties, pieceProperties)))
        return encoder.encode(pieceData)
        # TODO: update js code to properly handle json mimetype
        # return make_response(json.jsonify(pieceData), 200)
