"Ping"

from flask import current_app, make_response
from flask.views import MethodView
from flask_sse import sse


class PingView(MethodView):
    ""

    def post(self, puzzle_id):
        ""
        # TODO: get player id from cookie
        sse.publish(
            "PLAYER_ID",
            type="ping",
            channel="ping:{puzzle_id}".format(puzzle_id=puzzle_id),
        )
        response = make_response("pong", 200)
        return response
