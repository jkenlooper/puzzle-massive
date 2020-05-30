"""Artist - Run the puzzle_create jobs
Usage: puzzle-massive-artist [--config <file>]
       puzzle-massive-artist --help

Options:
    -h --help           Show this screen.
    --config <file>     Set config file. [default: site.cfg]
"""
from builtins import map
import os
import sys
from docopt import docopt

from flask import current_app
from rq import Worker, Queue, Connection

from api.app import make_app
from api.tools import loadConfig, get_redis_connection

# Preload libs
from api.jobs import pieceRenderer

listen = ["puzzle_create"]


def main():
    ""
    args = docopt(__doc__)
    config_file = args["--config"]
    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")
    redis_connection = get_redis_connection(config, decode_responses=False)
    app = make_app(config=config_file, cookie_secret=cookie_secret)

    with app.app_context():
        with Connection(redis_connection):
            artist = Worker(list(map(Queue, listen)))

            # If the render process has an exception
            artist.push_exc_handler(pieceRenderer.handle_render_fail)

            artist.work()


if __name__ == "__main__":
    main()
