from flask import current_app, request, abort, json, make_response
from flask.views import MethodView
import redis
import time

from api.app import db
from api.user import user_id_from_ip, user_not_banned
from api.database import fetch_query_string, rowify

encoder = json.JSONEncoder(indent=2, sort_keys=True)

redisConnection = redis.from_url('redis://localhost:6379/0/', decode_responses=True)

DAY = 24 * 60 * 60
ACTIVE_RANGE = 14 * DAY

class PlayerRanksView(MethodView):
    """
    """

    decorators = [user_not_banned]

    def get(self):
        ""
        ip = request.headers.get('X-Real-IP')
        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(ip))
        args = {}
        if request.args:
            args.update(request.args.to_dict(flat=True))
        start = args.get('start')
        count = args.get('count')
        if count == None:
            return make_response(encoder.encode({
                'msg': "missing count param"
            }), 400)

        count = int(count)
        if count > 45:
            return make_response(encoder.encode({
                'msg': "Count arg is too high"
            }), 400)


        cur = db.cursor()
        now = int(time.time())
        total_players = redisConnection.zcard('rank')
        player_rank = redisConnection.zrevrank('rank', user)
        if player_rank == None:
            player_rank = total_players - 1
        player_rank = player_rank + 1
        active_players = frozenset(map(int, redisConnection.zrevrangebyscore('timeline', '+inf', now - ACTIVE_RANGE)))

        if start == None:
            start = max(0, player_rank - int(count / 2))
        else:
            start = int(start)
        stop = start + count
        rank_slice = redisConnection.zrevrange('rank', start, stop, withscores=True)

        result = cur.execute(fetch_query_string('select-bit-icons-for-ranks.sql')).fetchall()
        (result, col_names) = rowify(result, cur.description)
        bit_icons = {}
        for item in result:
            bit_icons[item['user']] = item

        ranks = []
        for index, item in enumerate(rank_slice):
            (user, score) = map(int, item)
            bit_icon = bit_icons.get(user, {})
            ranks.append({
                "id": user,
                "score": score,
                "rank": start + index,
                "icon": bit_icon.get("icon", ''),
                "active": user in active_players,
                "bitactive": bool(bit_icon.get("active", 0))
            })

        player_ranks = {
            "total_players": total_players,
            "total_active_players": len(active_players),
            "player_rank": player_rank,
            "rank_slice": ranks,
        }

        cur.close()
        return encoder.encode(player_ranks)

class PuzzleStatsView(MethodView):
    """
    Return statistics on a puzzle.
    """

    decorators = [user_not_banned]

    def get(self, puzzle_id):
        ""
        ip = request.headers.get('X-Real-IP')
        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(ip))
        cur = db.cursor()
        result = cur.execute(fetch_query_string('_select-puzzle-by-puzzle_id.sql'), {
            'puzzle_id': puzzle_id
            }).fetchall()
        if not result:
            # 404 if puzzle does not exist
            abort(404)

        (result, col_names) = rowify(result, cur.description)
        puzzle = result[0].get('id')
        now = int(time.time())

        result = cur.execute(fetch_query_string('select-bit-icons-for-ranks.sql')).fetchall()
        (result, col_names) = rowify(result, cur.description)
        bit_icons = {}
        for item in result:
            bit_icons[item['user']] = item

        timeline = redisConnection.zrevrange('timeline:{puzzle}'.format(puzzle=puzzle), 0, -1, withscores=True)
        score_puzzle = redisConnection.zrange('score:{puzzle}'.format(puzzle=puzzle), 0, -1, withscores=True)
        user_score = dict(score_puzzle)
        user_rank = {}
        for index, item in enumerate(score_puzzle):
            user_rank[int(item[0])] = index + 1

        players = []
        for index, item in enumerate(timeline):
            (user, timestamp) = item
            bit_icon = bit_icons.get(int(user), {})
            players.append({
                "id": int(user),
                "score": int(user_score.get(user, 0)),
                "rank": user_rank.get(int(user), 0), # a 0 value means the player hasn't joined any pieces
                "seconds_from_now": int(now - timestamp),
                "icon": bit_icon.get("icon", ''),
                "bitactive": bool(bit_icon.get("active", 0))
            })

        # similar to queries/_recent-timeline-for-puzzle.sql
        puzzle_stats = {
            "now": now,
            "players": players
        }

        cur.close()
        return encoder.encode(puzzle_stats)
