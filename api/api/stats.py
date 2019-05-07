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
        player_rank = redisConnection.zrevrank('rank', user)
        total_players = redisConnection.zcard('rank')
        total_active_players = redisConnection.zcount('timeline', now - ACTIVE_RANGE, -1)

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
                "active": bit_icons.get("active", 0)
            })

        player_ranks = {
            "total_players": total_players,
            "total_active_players": total_active_players,
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
        status = result[0].get('status')
        now = int(time())

        timeline = redisConnection.zrange('timeline:{puzzle}'.format(puzzle=puzzle), 0, -1, withscores=True)
        score = dict(redisConnection.zrange('score:{puzzle}'.format(puzzle=puzzle), 0, -1, withscores=True))
        def set_entry(timeline_entry):
            (user, timestamp) = timeline_entry
            return {
                'player': int(user), # TODO: should include bit icon as well
                'seconds_from_now': now - int(timestamp),
                'score': int(score.get(user, 0))
            }

        # similar to queries/_recent-timeline-for-puzzle.sql
        puzzle_stats = {
            'players': list(map(set_entry, timeline))
        }

        cur.close()
        return encoder.encode(puzzle_stats)


# TODO: convert to client-side
#{% macro timePassed(seconds_from_now) -%}
#{# for testing
#{{ seconds_from_now }} =
##}
#    {% if seconds_from_now < 60 %}
#     less than a minute
#    {% elif seconds_from_now < 2 * 60 %}
#      1 minute
#    {% elif seconds_from_now < 60 * 60 %}
#      {{ seconds_from_now // 60 }} minutes
#    {% elif seconds_from_now < 60 * 60 * 2 %}
#      1 hour
#    {% elif seconds_from_now < 60 * 60 * 24 %}
#      {{ seconds_from_now // 60 // 60 }} hours
#    {% elif seconds_from_now < 60 * 60 * 24 * 2 %}
#      1 day
#    {% elif seconds_from_now < 60 * 60 * 24 * 14 %}
#      {{ seconds_from_now // 60 // 60 // 24 }} days
#    {% else %}
#      a long time
#    {% endif %}
#    ago
#{%- endmacro %}
