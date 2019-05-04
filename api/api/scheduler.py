import sys
from time import sleep, time, ctime, strftime, gmtime
import random
import logging

import sqlite3
import redis
from rq import Queue

from api.app import db
from api.database import rowify, read_query_file
from api.tools import loadConfig
from api.tools import deletePieceDataFromRedis
from api.timeline import archive_and_clear
from api.constants import REBUILD, COMPLETED, NEW_USER_STARTING_POINTS

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

SCHEDULER_INTERVAL = 5 if config['DEBUG'] else MINUTE
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
    "Auto rebuild completed puzzles that are no longer recent"
    interval = 15 * HOUR + 26 * MINUTE

    def __init__(self, id):
        super().__init__(id)
        self.queue = Queue('puzzle_create', connection=redisConnection)

    def do_task(self):
        logger.info("Doing task {task_name} {task_id}".format(**{
            'task_name':__class__.__name__,
            'task_id':self.id
        }))

        cur = db.cursor()
        (result, col_names) = rowify(cur.execute(read_query_file("select_random_puzzle_to_rebuild.sql"), {'status': COMPLETED}).fetchall(), cur.description)
        if result:
            for completed_puzzle in result:
                puzzle = completed_puzzle['id']

                logger.debug("found puzzle {id}".format(**completed_puzzle))
                # Update puzzle status to be REBUILD and change the piece count
                pieces = random.randint(max(int(config['MINIMUM_PIECE_COUNT']), completed_puzzle['pieces'] - 400), completed_puzzle['pieces'] + 400)
                cur.execute(read_query_file("update_status_puzzle_for_puzzle_id.sql"), {'puzzle_id': completed_puzzle['puzzle_id'], 'status': REBUILD, 'pieces': pieces})
                completed_puzzle['status'] = REBUILD
                completed_puzzle['pieces'] = pieces

                db.commit()

                # Delete any piece data from redis since it is no longer needed.
                query_select_all_pieces_for_puzzle = """select * from Piece where (puzzle = :puzzle)"""
                (all_pieces, col_names) = rowify(cur.execute(query_select_all_pieces_for_puzzle, {'puzzle': puzzle}).fetchall(), cur.description)
                deletePieceDataFromRedis(redisConnection, puzzle, all_pieces)

                job = self.queue.enqueue_call(
                    func='api.jobs.pieceRenderer.render', args=([completed_puzzle]), result_ttl=0,
                    timeout='24h'
                )

                archive_and_clear(puzzle, db, config.get('PUZZLE_ARCHIVE'))

        cur.close()
        db.commit()

class BumpMinimumDotsForPlayers(Task):
    "Increase dots for players that have less then the minimum"
    interval = DAY

    def do_task(self):
        logger.info("Doing task {task_name} {task_id}".format(**{
            'task_name':__class__.__name__,
            'task_id':self.id
        }))

        cur = db.cursor()
        cur.execute(read_query_file("update_points_to_minimum_for_all_users.sql"), {'minimum': NEW_USER_STARTING_POINTS})
        cur.close()
        db.commit()

class UpdateModifiedDateOnPuzzle(Task):
    "Update the m_date for all recently updated puzzles based on pcupdates redis sorted set"
    interval = 58
    last_update = int(time())

    def do_task(self):
        logger.info("Doing task {task_name} {task_id}".format(**{
            'task_name':__class__.__name__,
            'task_id':self.id
        }))

        cur = db.cursor()
        puzzles = map(int, redisConnection.zrangebyscore('pcupdates', self.last_update, '+inf'))
        self.last_update = int(time()) - 2 # allow some overlap
        for puzzle in puzzles:
            cur.execute(read_query_file("update_puzzle_m_date_to_now.sql"), {'puzzle': puzzle})
            logger.info("Updating puzzle m_date {0}".format(puzzle))
        cur.close()
        db.commit()

class UpdatePlayer(Task):
    "Update the User points, score, m_date from what has recently been put on redis"
    interval = 125
    first_run = True
    POINTS_CAP = 15000

    def do_task(self):
        logger.info("Doing task {task_name} {task_id}".format(**{
            'task_name':__class__.__name__,
            'task_id':self.id
        }))
        cur = db.cursor()

        user = redisConnection.spop('batchuser')
        while user:
            score = redisConnection.getset('batchscore:{user}'.format(user=user), value=0)
            redisConnection.expire('batchscore:{user}'.format(user=user), DAY)
            points = redisConnection.getset('batchpoints:{user}'.format(user=user), value=0)
            redisConnection.expire('batchpoints:{user}'.format(user=user), DAY)

            logger.debug("update user {id} with {points} points and score of {score}".format(**{'id':user, 'points':points, 'score':score}))
            cur.execute(read_query_file("update_user_points_and_m_date.sql"), {'id':user, 'points':points, 'score':score, 'POINTS_CAP':self.POINTS_CAP})
            cur.execute(read_query_file("update_bit_icon_expiration.sql"), {'user':user})

            user = redisConnection.spop('batchuser')

        if self.first_run:
            result = cur.execute(read_query_file("select_user_scores.sql")).fetchall(), cur.description
            logger.debug("user scores result {0}".format(result))
            if result:
                user_scores = dict(result[0])
                logger.debug("user scores dict {0}".format(user_scores))
                redisConnection.zadd('rank', user_scores)
            self.first_run = False

        cur.close()
        db.commit()

class UpdatePuzzleStats(Task):
    "Update the puzzle stats/timeline from what has recently been put on redis"
    interval = 60
    last_run = 0

    def do_task(self):
        logger.info("Doing task {task_name} {task_id}".format(**{
            'task_name':__class__.__name__,
            'task_id':self.id
        }))
        cur = db.cursor()

        puzzle = redisConnection.spop('batchpuzzle')
        while puzzle:
            last_batch = redisConnection.zrangebyscore('timeline:{puzzle}'.format(puzzle=puzzle), self.last_run, '+inf', withscores=True)
            for (user, update_timestamp) in last_batch:
                #self.last_run = int(max(self.last_run, update_timestamp))
                logger.debug("user: {user}, {update_timestamp}".format(user=user, update_timestamp=update_timestamp))
                user = int(user)
                points = int(redisConnection.getset('batchpoints:{puzzle}:{user}'.format(puzzle=puzzle, user=user), value=0) or '0')
                redisConnection.expire('batchpoints:{puzzle}:{user}'.format(puzzle=puzzle, user=user), DAY)
                if points != 0:
                    timestamp = strftime('%Y-%m-%d %H:%M:%S', gmtime(update_timestamp))
                    logger.debug("{timestamp} - bumping {points} points on {puzzle} for player: {player}".format(puzzle=puzzle, player=user, points=points, timestamp=timestamp))
                    cur.execute(read_query_file("insert_batchpoints_to_timeline.sql"), {
                      'puzzle': puzzle,
                      'player': user,
                      'points': points,
                      'timestamp': timestamp
                      })
            puzzle = redisConnection.spop('batchpuzzle')
        self.last_run = int(time())
        cur.close()
        db.commit()

def main():
    ""
    # Reset scheduler to start by removing any previous scheduled tasks
    redisConnection.delete(scheduler_key)

    now = int(time())
    task_registry = [
        AutoRebuildCompletedPuzzle,
        BumpMinimumDotsForPlayers,
        UpdateModifiedDateOnPuzzle,
        UpdatePlayer,
        UpdatePuzzleStats,
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
