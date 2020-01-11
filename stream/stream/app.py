import os
import logging

from flask import Flask
from flask_sse import sse

from stream.ping import PingView


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

    app.register_blueprint(sse, url_prefix="/stream")

    app.add_url_rule(
        "/ping/<puzzle_id>/", view_func=PingView.as_view("ping"),
    )

    @app.route("/send")
    def send_message():
        sse.publish("message", type="greeting", retry=5000)
        return "Message sent! {}".format(sse.redis)

    return app
