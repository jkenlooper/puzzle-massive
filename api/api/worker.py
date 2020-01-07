from builtins import map
import os

import redis
from rq import Worker, Queue, Connection

# Preload libs
from api.jobs import pieceTranslate

listen = ["puzzle_updates"]

# TODO: use app config REDIS_URL
redisConnection = redis.from_url("redis://localhost:6379/0/")

if __name__ == "__main__":
    with Connection(redisConnection):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
