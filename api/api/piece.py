from __future__ import absolute_import
from builtins import zip
from flask import abort, json, current_app, request
from flask.views import MethodView
import redis

from .app import db
from .database import fetch_query_string, rowify
from .constants import ACTIVE, IN_QUEUE
from .user import user_not_banned, user_id_from_ip

encoder = json.JSONEncoder(indent=2, sort_keys=True)

redisConnection = redis.from_url('redis://localhost:6379/0/', decode_responses=True)

class PuzzlePieceView(MethodView):
    """
    Get info about a single puzzle piece.
    """
    decorators = [user_not_banned]

    def get(self, puzzle_id, piece):

        ip = request.headers.get('X-Real-IP')
        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(ip))
        cur = db.cursor()
        result = cur.execute(fetch_query_string('select_puzzle_id_by_puzzle_id.sql'), {
            'puzzle_id': puzzle_id
            }).fetchall()
        if not result:
            # 404 if puzzle or piece does not exist
            abort(404)

        (result, col_names) = rowify(result, cur.description)
        puzzle = result[0].get('puzzle')
        cur.close()

        # Only allow if there is data in redis
        if not redisConnection.zscore('pcupdates', puzzle):
            abort(400)

        # Expire the token at the lock timeout since it shouldn't be used again
        redisConnection.delete("pctoken:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece))
        redisConnection.delete('token:{}'.format(user))

        # Fetch just the piece properties
        publicPieceProperties = ('x', 'y', 'rotate', 's', 'w', 'h', 'b')
        pieceProperties = redisConnection.hmget('pc:{puzzle}:{piece}'.format(puzzle=puzzle, piece=piece), *publicPieceProperties)
        pieceData = dict(list(zip(publicPieceProperties, pieceProperties)))
        return encoder.encode(pieceData)
