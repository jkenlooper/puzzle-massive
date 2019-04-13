from builtins import map
query_idle_puzzles = """
select * from Puzzle where m_date < datetime('now', '-10 minutes') order by m_date
"""

# TODO: listen for jobs? When puzzle-pieces are moved to redis then publish
# a janitor job to make more space if necessary?

# Check redis info memory to see if it's at threshold
# TODO: add m_date to redis for each piece move. (keep DB m_date for now)
# Find idle puzzles sorted by m_date
# Intersect with puzzles in redis
# For each puzzle convertPiecesToDB and recheck redis info memory

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
        worker.work()


if __name__ == '__main__':
    main()
