import sys
from time import sleep, time
import logging

import sqlite3
import redis

from api.app import db
from api.database import rowify, read_query_file
from api.tools import loadConfig
from api.timeline import archive_and_clear

# Get the args from the janitor and connect to the database
config_file = sys.argv[1]
config = loadConfig(config_file)

db_file = config['SQLITE_DATABASE_URI']
db = sqlite3.connect(db_file)

redisConnection = redis.from_url('redis://localhost:6379/0/', decode_responses=True)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if config['DEBUG'] else logging.INFO)

SCHEDULER_INTERVAL = 5
HOUR = 3600 # hour in seconds
DAY = HOUR * 24
MINUTE = 60 # minute in seconds

TASKS = [
    'task_auto_rebuild_completed_puzzle',
    'bump_minimum_dots_for_players'
]
scheduler_key = 'sc'

def main():
    ""
    now = int(time())
    # a little crazy, but it does this: redisConnection.zadd(scheduler_key, {0: now, 1: now})
    redisConnection.zadd(scheduler_key, dict(zip(range(len(TASKS)), list(map(lambda x: now, range(len(TASKS)))))))
    while True:
        now = int(time())
        # Get list of tasks on the schedule that are past the now time.
        tasks = list(map(int, redisConnection.zrangebyscore(scheduler_key, 0, now)))

        # Cycle over each and call the task
        for taskid in tasks:
            globals()[TASKS[taskid]]()

        sleep(SCHEDULER_INTERVAL)

def bump_minimum_dots_for_players():
    "Increase dots for players that have less then the minimum"
    interval = DAY
    task_id = 1
    task_name = TASKS[task_id]

    logger.info("do task: {0}".format(task_name))

    now = int(time())
    redisConnection.zadd(scheduler_key, {task_id: now + interval})

def task_auto_rebuild_completed_puzzle():
    "Auto rebuild a completed puzzle that is no longer recent"
    interval = MINUTE
    task_id = 0
    task_name = TASKS[task_id]

    logger.info("do task: {0}".format(task_name))

    cur = db.cursor()
    (result, col_names) = rowify(cur.execute(read_query_file("_select-puzzles-for-queue--complete.sql")).fetchall(), cur.description)
    if result:
        completed_puzzle = result[0]
        #print(completed_puzzle)
        logger.debug("found puzzle {id}".format(**completed_puzzle))
        # TODO: update puzzleData for this puzzle to rebuild
        #job = current_app.createqueue.enqueue_call(
        #    func='api.jobs.pieceRenderer.render', args=([puzzleData]), result_ttl=0,
        #    timeout='24h'
        #)
        #archive_and_clear(puzzle)

    now = int(time())
    redisConnection.zadd(scheduler_key, {task_id: now + interval})

if __name__ == '__main__':
    main()
