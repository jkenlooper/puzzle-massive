from builtins import map
import os
import sys

from rq import Worker, Queue, Connection

from api.app import redis_connection, make_app
from api.tools import loadConfig, get_redis_connection

# Preload libs
from api.jobs import convertPiecesToDB


def main():
    ""
    listen = ["puzzle_cleanup"]
    with Connection(redis_connection):
        worker = Worker(list(map(Queue, listen)))

        # If the render process has an exception
        worker.push_exc_handler(convertPiecesToDB.handle_fail)

        worker.work()


if __name__ == "__main__":
    config_file = sys.argv[1]
    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")
    app = make_app(config=config, cookie_secret=cookie_secret)

    with app.app_context():
        main()
