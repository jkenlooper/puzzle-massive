"""Worker - Run the puzzle_updates jobs
Usage: puzzle-massive-worker [--config <file>] <queue_name>
       puzzle-massive-worker --help

Options:
    -h --help           Show this screen.
    --config <file>     Set config file. [default: site.cfg]
"""

from builtins import map
import os
import sys
from docopt import docopt
import time

from flask import current_app
from rq import Worker, Queue, Connection

from api.app import make_app
from api.tools import loadConfig, get_redis_connection

# Preload libs
from api.jobs import pieceTranslate


def main():
    ""
    args = docopt(__doc__)
    config_file = args["--config"]
    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")
    redis_connection = get_redis_connection(config, decode_responses=False)
    app = make_app(config=config_file, cookie_secret=cookie_secret)
    queue_name = args["<queue_name>"]
    listen = [queue_name]

    with app.app_context():
        with Connection(redis_connection):
            worker = Worker(list(map(Queue, listen)))

            # TODO: handle exceptions
            # worker.push_exc_handler(pieceTranslate.handle_piece_error)

            # Register the queue name
            redis_connection.sadd("pzq_register", queue_name)

            worker.work()

            # TODO: Use a pipe and find all puzzles that have set the 'q' to this
            # queue before removing the registered queue.

            redis_connection.expire(
                "pzq_activity:{queue_name}".format(queue_name=queue_name), 0
            )
            redis_connection.srem("pzq_register", queue_name)


if __name__ == "__main__":
    main()
