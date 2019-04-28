import sys
from time import sleep, time, ctime
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


HOUR = 3600 # hour in seconds
DAY = HOUR * 24
MINUTE = 60 # minute in seconds

SCHEDULER_INTERVAL = MINUTE
scheduler_key = 'sc'

class Task:
    interval = 5

    def __init__(self, id):
        self.id = id

    def __call__(self):
        self.do_task()
        now = int(time())
        due = now + self.interval
        logger.info("Setting task {task_name} {task_id} due date to {format_due}".format(**{
            'format_due':ctime(due),
            'task_name':__class__.__name__,
            'task_id':self.id
        }))
        redisConnection.zadd(scheduler_key, {self.id: due})

    def do_task(self):
        logger.info('do task')

class AutoRebuildCompletedPuzzle(Task):
    "Auto rebuild a completed puzzle that is no longer recent"
    interval = MINUTE

    def do_task(self):
        logger.info("Doing task {task_name} {task_id}".format(**{
            'task_name':__class__.__name__,
            'task_id':self.id
        }))

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
        cur.close()

class BumpMinimumDotsForPlayers(Task):
    "Increase dots for players that have less then the minimum"
    interval = DAY

    def do_task(self):
        logger.info("Doing task {task_name} {task_id}".format(**{
            'task_name':__class__.__name__,
            'task_id':self.id
        }))

def main():
    ""
    # Reset scheduler to start by removing any previous scheduled tasks
    redisConnection.delete(scheduler_key)

    now = int(time())
    task_registry = [
        AutoRebuildCompletedPuzzle,
        BumpMinimumDotsForPlayers,
    ]
    tasks = {}
    for index in range(len(task_registry)):
        # Create each task with an id corresponding to the index
        tasks[index] = task_registry[index](index)

    task_ids_scheduled_to_now = dict(zip(tasks.keys(), map(lambda x: now, range(len(tasks)))))

    # reset all tasks to be scheduled now
    redisConnection.zadd(scheduler_key, task_ids_scheduled_to_now)

    while True:
        now = int(time())
        # Get list of tasks on the schedule that are due.
        task_ids = list(map(int, redisConnection.zrangebyscore(scheduler_key, 0, now)))

        # Cycle over each and call the task
        for task_id in task_ids:
            tasks[task_id]()

        sleep(SCHEDULER_INTERVAL)

if __name__ == '__main__':
    main()
