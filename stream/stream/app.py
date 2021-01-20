import os
import logging

from flask import Flask, request, current_app, abort
from flask_sse import sse
import requests

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


class StreamApp(Flask):
    "Stream App"


def make_app(config=None, **kw):
    app = StreamApp("stream")

    if config:
        config_file = (
            config if config[0] == os.sep else os.path.join(os.getcwd(), config)
        )
        app.config.from_pyfile(config_file)

    app.config.update(kw)

    @app.errorhandler(400)
    def invalid_request(error):
        return "Not valid", 400

    @app.errorhandler(403)
    def forbidden_request(error):
        return "No access", 403

    @app.errorhandler(404)
    def notfound_request(error):
        return "Not found", 404

    @app.errorhandler(500)
    def error_request(error):
        return "Error", 500

    @sse.before_request
    def check_puzzle_status():
        # response = {"message": "", "name": "error"}
        channel_name = request.args.get("channel")
        if channel_name == None:
            abort(400)
        elif channel_name.startswith("puzzle:"):
            puzzle_id = channel_name[len("puzzle:") :]

            r = requests.get(
                "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                    HOSTAPI=current_app.config["HOSTAPI"],
                    PORTAPI=current_app.config["PORTAPI"],
                    puzzle_id=puzzle_id,
                ),
            )
            if r.status_code >= 400:
                abort(r.status_code)
            try:
                result = r.json()
            except ValueError as err:
                abort(500)
            if result.get("status") not in (
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
                abort(400)

            return None
        else:
            abort(400)

    app.register_blueprint(sse, url_prefix="/stream")

    return app
