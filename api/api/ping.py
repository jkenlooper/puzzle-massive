"Ping"
import time
import uuid

from flask import current_app, make_response, request, json
from flask.views import MethodView
from flask_sse import sse

from api.app import db, redis_connection
from api.user import user_not_banned, user_id_from_ip
from api.database import fetch_query_string, rowify
from api.constants import ACTIVE


class PingPuzzleView(MethodView):
    "Handle requests to ping a puzzle and keep the connection open."

    def post(self, puzzle_id):
        "Ping and record the time in milliseconds for this player."
        now_ms = int(time.time() * 1000)
        response = {"message": "", "name": "", "token": ""}

        user = current_app.secure_cookie.get(u"user") or user_id_from_ip(
            request.headers.get("X-Real-IP"), skip_generate=True
        )

        if user == None:
            response["message"] = "Player not currently logged in."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        user = int(user)

        cur = db.cursor()

        # Validate the puzzle_id
        result = cur.execute(
            fetch_query_string("select_viewable_puzzle_id.sql"),
            {"puzzle_id": puzzle_id},
        ).fetchall()
        if not result:
            response["message"] = "Invalid puzzle id."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)
        else:
            (result, col_names) = rowify(result, cur.description)
            puzzle = result[0].get("puzzle")
            status = result[0].get("status")
            if status != ACTIVE:
                response["message"] = "Puzzle not active"
                response["name"] = "invalid"
                return make_response(json.jsonify(response), 200)

        # publish to the puzzle channel the ping with the user id.  This will
        # allow that player to determine their latency.
        token = uuid.uuid4().hex
        # TODO: record token in redis for a minute
        redis_connection.set(
            "pingtoken:{puzzle}:{user}".format(puzzle=puzzle, user=user),
            "{token}:{now_ms}".format(token=token, now_ms=now_ms),
            ex=60,
        )

        sse.publish(
            user, type="ping", channel=puzzle_id,
        )
        response["message"] = "ping accepted"
        response["data"]["token"] = token
        response["name"] = "accepted"
        response = make_response(json.jsonify(response), 202)
        return response

    def patch(self, puzzle_id):
        "Pong. Determine the latency for this player."
        # TODO: validate the token for the player and respond with the latency
        now_ms = int(time.time() * 1000)
        response = {"message": "", "name": "", "data": {"latency": 0}}

        user = current_app.secure_cookie.get(u"user") or user_id_from_ip(
            request.headers.get("X-Real-IP"), skip_generate=True
        )

        if user == None:
            response["message"] = "Player not currently logged in."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        user = int(user)

        # Publish to the puzzle channel the latency with the user id.
        # TODO: show latency to other players?
        sse.publish(
            user, type="latency", channel=puzzle_id,
        )
        response["message"] = "Latency"
        response["data"]["latency"] = 123  # TODO:
        response["name"] = "success"
        response = make_response(json.jsonify(response), 200)
        return response
