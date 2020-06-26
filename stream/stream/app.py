import os
import logging

from werkzeug.local import LocalProxy
from flask import Flask, g, request, current_app, make_response, abort, json
from flask_sse import sse

from api.flask_secure_cookie import SecureCookie
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
from api.user import user_id_from_ip
from api.tools import get_db, files_loader


class StreamApp(Flask):
    "Stream App"


def set_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = get_db(current_app.config)
    return db


db = LocalProxy(set_db)


def make_app(config=None, **kw):
    app = StreamApp("stream")

    if config:
        config_file = (
            config if config[0] == os.sep else os.path.join(os.getcwd(), config)
        )
        app.config.from_pyfile(config_file)

    app.config.update(kw)

    app.secure_cookie = SecureCookie(
        app, cookie_secret=app.config.get("SECURE_COOKIE_SECRET")
    )
    app.queries = files_loader("queries")

    @app.teardown_appcontext
    def teardown_db(exception):
        db = getattr(g, "_database", None)
        if db is not None:
            db.close()

    @app.errorhandler(400)
    def invalid_request(error):
        return "Not valid", 400

    @app.errorhandler(403)
    def invalid_request(error):
        return "No access", 403

    @sse.before_request
    def check_puzzle_status():
        # response = {"message": "", "name": "error"}
        channel_name = request.args.get("channel")
        if channel_name == None:
            abort(400)
        elif channel_name.startswith("puzzle:"):
            puzzle_id = channel_name[len("puzzle:") :]

            # check if player is logged in
            user = current_app.secure_cookie.get(
                u"user"
            ) or current_app.secure_cookie.get(u"shareduser")
            if user == None:
                abort(403)
            user = int(user)

            cur = db.cursor()

            # Validate the puzzle_id
            result = cur.execute(
                fetch_query_string("select-all-from-puzzle-by-puzzle_id.sql"),
                {"puzzle_id": puzzle_id},
            ).fetchall()
            if not result:
                abort(400)
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
                    # response["message"] = "Puzzle not active"
                    # response["name"] = "invalid"
                    # abort(make_response(json.jsonify(response), 400))
                    sse.publish(
                        "Puzzle no longer valid",
                        type="invalid",
                        channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_id),
                    )

                # return None
            return None
        else:
            abort(400)

    app.register_blueprint(sse, url_prefix="/stream")

    return app
