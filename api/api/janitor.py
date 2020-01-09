from builtins import map
import os

from rq import Worker, Queue, Connection

from api.tools import loadConfig, get_redis_connection

# Preload libs
from api.jobs import convertPiecesToDB

# Get the args
config_file = sys.argv[1]
config = loadConfig(config_file)

listen = ["puzzle_cleanup"]

redis_connection = get_redis_connection(config)


def main():
    ""
    with Connection(redis_connection):
        worker = Worker(list(map(Queue, listen)))

        # If the render process has an exception
        worker.push_exc_handler(convertPiecesToDB.handle_fail)

        worker.work()


if __name__ == "__main__":
    main()
