"""Janitor - Run the puzzle_cleanup jobs
Usage: puzzle-massive-janitor [--config <file>]
       puzzle-massive-janitor --help

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
from api.jobs import convertPiecesToDB, piece_forker, piece_reset

listen = ["puzzle_cleanup"]


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
            worker = Worker(list(map(Queue, listen)))

            # If the render process has an exception
            worker.push_exc_handler(convertPiecesToDB.handle_fail)

            worker.work()


if __name__ == "__main__":
    main()
