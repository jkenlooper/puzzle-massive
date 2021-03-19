"Ping"
import time
import uuid

from flask import current_app, make_response, request, json
from flask.views import MethodView
from flask_sse import sse

from api.app import db, redis_connection
from api.user import user_not_banned, user_id_from_ip
from api.database import fetch_query_string, rowify
from api.constants import (
    ACTIVE,
    IN_QUEUE,
    COMPLETED,
    FROZEN,
    BUGGY_UNLISTED,
    NEEDS_MODERATION,
    REBUILD,
    IN_RENDER_QUEUE,
    RENDERING,
    RENDERING_FAILED,
    MAINTENANCE,
)

# Set ping token expire to be a little over 5 minutes
PING_EXPIRE = 300 + 60


def get_pingtoken_key(puzzle, user, token):
    "Store the ping timestamp value that expires within a minute."
    return "pingtoken:{puzzle}:{user}:{token}".format(
        puzzle=puzzle, user=user, token=token
    )


def get_ping_key(puzzle):
    "sorted set for recording the reply timestamps for players pinging a puzzle"
    return "ping:{puzzle}".format(puzzle=puzzle)


class PingPuzzleView(MethodView):
    "Handle requests to ping a puzzle and keep the connection open."

    def post(self, puzzle_id):
        "Ping and record the time in milliseconds for this player."
        now_ms = int(time.time() * 1000)
        response = {"message": "", "name": ""}

        user = current_app.secure_cookie.get(u"user") or user_id_from_ip(
            request.headers.get("X-Real-IP"),
            skip_generate=True,
            validate_shared_user=False,
        )

        if user is None:
            response["message"] = "Player not currently logged in."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        user = int(user)

        cur = db.cursor()

        # Validate the puzzle_id
        result = cur.execute(
            fetch_query_string("select-all-from-puzzle-by-puzzle_id.sql"),
            {"puzzle_id": puzzle_id},
        ).fetchall()
        if not result:
            response["message"] = "Puzzle not available"
            response["name"] = "invalid"
            cur.close()
            return make_response(json.jsonify(response), 400)
        else:
            (result, col_names) = rowify(result, cur.description)
            puzzle = result[0].get("puzzle")
            status = result[0].get("status")
            if status not in (
                ACTIVE,
                IN_QUEUE,
                COMPLETED,
                FROZEN,
                BUGGY_UNLISTED,
                NEEDS_MODERATION,
                REBUILD,
                IN_RENDER_QUEUE,
                RENDERING,
                RENDERING_FAILED,
                MAINTENANCE,
            ):
                response["message"] = "Puzzle no longer valid"
                response["name"] = "invalid"
                cur.close()
                sse.publish(
                    "Puzzle no longer valid",
                    type="invalid",
                    channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_id),
                )
                return make_response(json.jsonify(response), 200)

        cur.close()
        # publish to the puzzle channel the ping with the user id.  This will
        # allow that player to determine their latency.
        token = uuid.uuid4().hex[:4]
        pingtoken_key = get_pingtoken_key(puzzle, user, token)
        redis_connection.setex(pingtoken_key, 60, now_ms)

        current_app.logger.debug("publish ping {puzzle_id}".format(puzzle_id=puzzle_id))
        sse.publish(
            "{user}:{token}".format(user=user, token=token),
            type="ping",
            channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_id),
        )
        response["message"] = "ping accepted"
        response["name"] = "accepted"
        response = make_response(json.jsonify(response), 202)
        return response

    def patch(self, puzzle_id):
        "Pong. Determine the latency for this player."
        response = {"message": "", "name": "", "data": {"latency": 0}}

        args = {}
        xhr_data = request.get_json()
        if xhr_data:
            args.update(xhr_data)
        if request.form:
            args.update(request.form.to_dict(flat=True))

        token = args.get("token")
        if token is None:
            response["message"] = "No token"
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        user = current_app.secure_cookie.get(u"user") or user_id_from_ip(
            request.headers.get("X-Real-IP"),
            skip_generate=True,
            validate_shared_user=False,
        )

        if user is None:
            response["message"] = "Player not currently logged in."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        user = int(user)

        cur = db.cursor()

        # Validate the puzzle_id
        result = cur.execute(
            fetch_query_string("select-all-from-puzzle-by-puzzle_id.sql"),
            {"puzzle_id": puzzle_id},
        ).fetchall()
        if not result:
            response["message"] = "Puzzle not available"
            response["name"] = "invalid"
            cur.close()
            return make_response(json.jsonify(response), 400)
        else:
            (result, col_names) = rowify(result, cur.description)
            puzzle = result[0].get("puzzle")
            status = result[0].get("status")
            if status not in (
                ACTIVE,
                IN_QUEUE,
                COMPLETED,
                FROZEN,
                BUGGY_UNLISTED,
                NEEDS_MODERATION,
                REBUILD,
                IN_RENDER_QUEUE,
                RENDERING,
                RENDERING_FAILED,
                MAINTENANCE,
            ):
                response["message"] = "Puzzle no longer valid"
                response["name"] = "invalid"
                cur.close()
                sse.publish(
                    "Puzzle no longer valid",
                    type="invalid",
                    channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_id),
                )
                return make_response(json.jsonify(response), 200)

        cur.close()
        # Determine latency for the player and record timestamp in sorted set.
        pingtoken_key = get_pingtoken_key(puzzle, user, token)
        ping_start = redis_connection.get(pingtoken_key)
        redis_connection.delete(pingtoken_key)
        ping_end = int(time.time() * 1000)
        if not ping_start:
            response["message"] = "Ignoring error when determining latency."
            response["name"] = "ignored"
            return make_response(json.jsonify(response), 200)
        ping_start = int(ping_start)
        ping_key = get_ping_key(puzzle)
        redis_connection.zadd(ping_key, {user: ping_end})
        redis_connection.expire(ping_key, PING_EXPIRE)

        latency = ping_end - ping_start

        # Record the latency for the player
        redis_connection.lpush(
            "latency",
            "{user}:{timestamp}:{latency}".format(
                user=user, timestamp=ping_end, latency=latency
            ),
        )
        # Keep only the last 1000 entries to latency
        redis_connection.ltrim("latency", 0, 999)

        response["message"] = "Latency"
        response["data"]["latency"] = latency
        response["name"] = "success"
        response = make_response(json.jsonify(response), 200)
        return response
