import os

import redis
from rq import Worker, Queue, Connection

#Preload libs
from api.jobs import pieceRenderer

listen = ['puzzle_create']
# TODO: append 'puzzle_rebuild' to the listen list

# TODO: use app config REDIS_URI
redisConnection = redis.from_url('redis://localhost:6379/0/')

def main():
    ""
    with Connection(redisConnection):
        artist = Worker(list(map(Queue, listen)))

        # If the render process has an exception
        artist.push_exc_handler(pieceRenderer.handle_render_fail)

        artist.work()

if __name__ == '__main__':
    main()

