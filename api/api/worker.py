from builtins import map
import os

from rq import Worker, Queue, Connection

from api.tools import loadConfig, get_redis_connection

# Preload libs
from api.jobs import pieceTranslate

# Get the args
config_file = sys.argv[1]
config = loadConfig(config_file)

listen = ["puzzle_updates"]

redis_connection = get_redis_connection(config)

if __name__ == "__main__":
    with Connection(redis_connection):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
