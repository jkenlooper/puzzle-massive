from flask import current_app, request, abort, json, make_response
from flask.views import MethodView
import redis
import time

from api.app import db
from api.user import user_id_from_ip, user_not_banned
from api.database import fetch_query_string, rowify

encoder = json.JSONEncoder(indent=2, sort_keys=True)

redisConnection = redis.from_url("redis://localhost:6379/0/", decode_responses=True)

DAY = 24 * 60 * 60
ACTIVE_RANGE = 14 * DAY


class PlayerRanksView(MethodView):
    """
    """

    decorators = [user_not_banned]

    def get(self):
        ""
        ip = request.headers.get("X-Real-IP")
        user = current_app.secure_cookie.get(u"user") or user_id_from_ip(ip)
        if user != None:
            user = int(user)
        args = {}
        if request.args:
            args.update(request.args.to_dict(flat=True))
        count = args.get("count")
        if count == None:
            return make_response(encoder.encode({"msg": "missing count param"}), 400)

        count = int(count)
        if count > 45:
            return make_response(encoder.encode({"msg": "Count arg is too high"}), 400)

        cur = db.cursor()
        now = int(time.time())
        active_players = frozenset(
            map(
                int,
                redisConnection.zrevrangebyscore(
                    "timeline", "+inf", now - ACTIVE_RANGE
                ),
            )
        )

        rank_slice = redisConnection.zrevrange("rank", 0, -1, withscores=True)

        ranks = []
        has_user_in_ranks = False
        user_in_ranks_index = -1
        for index, item in enumerate(rank_slice):
            (player, score) = map(int, item)
            if not has_user_in_ranks and player == user:
                has_user_in_ranks = True
                user_in_ranks_index = len(ranks)
            if player in active_players or player == user:
                ranks.append(
                    {"id": player, "score": score,}
                )

        ranks_near_user = []
        if has_user_in_ranks:
            start = max(0, user_in_ranks_index - int(count / 2))
            end = min(len(ranks), user_in_ranks_index + int(count / 2))
            ranks_near_user = ranks[start:end]

        player_ranks = {
            "rank_slice": ranks_near_user,
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
        cur = db.cursor()
        result = cur.execute(
            fetch_query_string("_select-puzzle-by-puzzle_id.sql"),
            {"puzzle_id": puzzle_id},
        ).fetchall()
        if not result:
            # 404 if puzzle does not exist
            abort(404)

        (result, col_names) = rowify(result, cur.description)
        puzzle = result[0].get("id")
        now = int(time.time())

        timeline = redisConnection.zrevrange(
            "timeline:{puzzle}".format(puzzle=puzzle), 0, -1, withscores=True
        )
        score_puzzle = redisConnection.zrange(
            "score:{puzzle}".format(puzzle=puzzle), 0, -1, withscores=True
        )
        user_score = dict(score_puzzle)
        user_rank = {}
        for index, item in enumerate(score_puzzle):
            user_rank[int(item[0])] = index + 1

        players = []
        for index, item in enumerate(timeline):
            (user, timestamp) = item
            players.append(
                {
                    "id": int(user),
                    "score": int(user_score.get(user, 0)),
                    "rank": user_rank.get(
                        int(user), 0
                    ),  # a 0 value means the player hasn't joined any pieces
                    "seconds_from_now": int(now - timestamp),
                }
            )

        puzzle_stats = {"now": now, "players": players}

        cur.close()
        return encoder.encode(puzzle_stats)


class PuzzleActiveCountView(MethodView):
    """
    Return active player count on a puzzle.
    """

    decorators = [user_not_banned]

    def get(self, puzzle_id):
        ""
        ip = request.headers.get("X-Real-IP")
        user = int(current_app.secure_cookie.get(u"user") or user_id_from_ip(ip))
        cur = db.cursor()
        result = cur.execute(
            fetch_query_string("select_viewable_puzzle_id.sql"),
            {"puzzle_id": puzzle_id},
        ).fetchall()
        if not result:
            # 404 if puzzle does not exist
            abort(404)

        (result, col_names) = rowify(result, cur.description)
        puzzle = result[0].get("puzzle")
        status = result[0].get("status")
        now = int(time.time())

        count = (
            redisConnection.zcount(
                "timeline:{puzzle}".format(puzzle=puzzle), now - 5 * 60, "+inf"
            )
            or 0
        )

        player_active_count = {"now": now, "count": count}

        cur.close()
        return json.jsonify(player_active_count)


class PlayerStatsView(MethodView):
    ""

    decorators = [user_not_banned]

    def get(self):
        ""
        now = int(time.time())
        since = now - ACTIVE_RANGE
        total_active_player_count = redisConnection.zcount("timeline", since, "+inf")
        return json.jsonify({"totalActivePlayers": total_active_player_count})
