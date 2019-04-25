from builtins import map
import os

import redis
from rq import Worker, Queue, Connection

#Preload libs
from api.jobs import convertPiecesToDB

listen = ['puzzle_cleanup']

# TODO: use app config REDIS_URI
redisConnection = redis.from_url('redis://localhost:6379/0/')


def main():
    ""
    with Connection(redisConnection):
        worker = Worker(list(map(Queue, listen)))

        # If the render process has an exception
        worker.push_exc_handler(convertPiecesToDB.handle_fail)

        worker.work()


if __name__ == '__main__':
    main()
