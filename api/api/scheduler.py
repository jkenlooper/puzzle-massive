"""Scheduler - Run tasks at predefined intervals

Usage: puzzle-massive-scheduler [--config <file>]
       puzzle-massive-scheduler [--config <file>] [--task <task_name>]
       puzzle-massive-scheduler --list
       puzzle-massive-scheduler --help

Options:
    -h --help           Show this screen.
    --config <file>     Set config file. [default: site.cfg]
    --task <task_name>  Run only one task instead of all of them.
    --list              List available tasks
"""

from docopt import docopt
from time import sleep, time, ctime, strftime, gmtime
import random

from flask import current_app
from rq import Queue
import requests

from api.database import rowify, read_query_file, fetch_query_string
from api.app import redis_connection, db, make_app
from api.tools import loadConfig
from api.tools import deletePieceDataFromRedis
from api.timeline import archive_and_clear
from api.constants import (
    ACTIVE,
    IN_QUEUE,
    QUEUE_INACTIVE,
    REBUILD,
    COMPLETED,
    SKILL_LEVEL_RANGES,
    QUEUE_END_OF_LINE,
)
from api.notify import send_message

HOUR = 3600  # hour in seconds
DAY = HOUR * 24
MINUTE = 60  # minute in seconds

SCHEDULER_INTERVAL = 1
scheduler_key = "sc"


class Task:
    interval = 5

    def __init__(self, id=None, task_name="Task"):
        self.id = id
        self.task_name = task_name

    def __call__(self):
        self.do_task()
        if self.id == None:
            # The id may be None if the task is being run manually.  Running
            # a task manually shouldn't change the schedule.
            return
        now = int(time())
        due = now + self.interval
        current_app.logger.debug(
            "{format_due} - task {task_name} {task_id} due date".format(
                **{
                    "format_due": ctime(due),
                    "task_name": self.task_name,
                    "task_id": self.id,
                }
            )
        )
        redis_connection.zadd(scheduler_key, {self.id: due})

    def log_task(self):
        current_app.logger.info(
            "Doing task {task_name} {task_id}".format(
                **{"task_name": self.task_name, "task_id": self.id}
            )
        )

    def do_task(self):
        current_app.logger.debug(
            "{task_name} {task_id} task description:\n {doc}".format(
                **{"task_name": self.task_name, "task_id": self.id, "doc": self.__doc__}
            )
        )


class AutoRebuildCompletedPuzzle(Task):
    "Auto rebuild completed puzzles that are no longer recent"
    interval = 26 * MINUTE

    # The minimum count of incomplete puzzles before the auto rebuild task will
    # find random puzzles to rebuild.
    minimum_count = 6

    def __init__(self, id=None):
        super().__init__(id, __class__.__name__)
        self.queue = Queue("puzzle_create", connection=redis_connection)

    def do_task(self):
        super().do_task()
        made_change = False

        cur = db.cursor()
        for (low, high) in SKILL_LEVEL_RANGES:
            in_queue_puzzle_count = cur.execute(
                read_query_file("get_in_queue_puzzle_count.sql"),
                {"low": low, "high": high},
            ).fetchone()[0]
            if in_queue_puzzle_count <= self.minimum_count:
                (result, col_names) = rowify(
                    cur.execute(
                        read_query_file("select_random_puzzle_to_rebuild.sql"),
                        {"status": COMPLETED, "low": low, "high": high},
                    ).fetchall(),
                    cur.description,
                )
                if result:
                    for completed_puzzle in result:
                        puzzle = completed_puzzle["id"]

                        current_app.logger.debug(
                            "found puzzle {id}".format(**completed_puzzle)
                        )
                        # Update puzzle status to be REBUILD and change the piece count
                        pieces = random.randint(
                            max(
                                int(current_app.config["MINIMUM_PIECE_COUNT"]),
                                max(completed_puzzle["pieces"] - 400, low),
                            ),
                            min(high - 1, completed_puzzle["pieces"] + 400),
                        )
                        r = requests.patch(
                            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                                HOSTAPI=current_app.config["HOSTAPI"],
                                PORTAPI=current_app.config["PORTAPI"],
                                puzzle_id=completed_puzzle["puzzle_id"],
                            ),
                            json={
                                "status": REBUILD,
                                "pieces": pieces,
                                "queue": QUEUE_END_OF_LINE,
                            },
                        )
                        if r.status_code != 200:
                            current_app.logger.warning(
                                "Puzzle details api error. Could not set puzzle status to rebuild. Skipping {puzzle_id}".format(
                                    **completed_puzzle
                                )
                            )
                            continue
                        completed_puzzle["status"] = REBUILD
                        completed_puzzle["pieces"] = pieces

                        # db.commit()

                        # Delete any piece data from redis since it is no longer needed.
                        query_select_all_pieces_for_puzzle = (
                            """select * from Piece where (puzzle = :puzzle)"""
                        )
                        (all_pieces, col_names) = rowify(
                            cur.execute(
                                query_select_all_pieces_for_puzzle, {"puzzle": puzzle}
                            ).fetchall(),
                            cur.description,
                        )
                        deletePieceDataFromRedis(redis_connection, puzzle, all_pieces)

                        job = self.queue.enqueue_call(
                            func="api.jobs.pieceRenderer.render",
                            args=([completed_puzzle]),
                            result_ttl=0,
                            timeout="24h",
                        )

                        archive_and_clear(puzzle)
                    made_change = True

        cur.close()
        db.commit()
        if made_change:
            self.log_task()


class BumpMinimumDotsForPlayers(Task):
    "Increase dots for players that have less then the minimum"
    interval = DAY

    def __init__(self, id=None):
        super().__init__(id, __class__.__name__)

    def do_task(self):
        super().do_task()

        cur = db.cursor()
        # TODO: use newapi/internal/
        result = cur.execute(
            read_query_file("update_points_to_minimum_for_all_users.sql"),
            {"minimum": current_app.config["NEW_USER_STARTING_POINTS"]},
        )
        if result.rowcount:
            self.log_task()
        cur.close()
        db.commit()


class UpdateModifiedDateOnPuzzle(Task):
    "Update the m_date for all recently updated puzzles based on pcupdates redis sorted set"
    interval = 15
    first_run = True
    last_update = int(time())

    def __init__(self, id=None):
        super().__init__(id, __class__.__name__)

    def do_task(self):
        super().do_task()

        cur = db.cursor()

        if self.first_run:
            result = cur.execute(
                fetch_query_string("select_most_recent_puzzle_by_m_date.sql")
            ).fetchone()
            if result and len(result):
                self.last_update = int(result[0]) - self.interval

            self.first_run = False

        puzzles = redis_connection.zrangebyscore(
            "pcupdates", self.last_update, "+inf", withscores=True
        )
        self.last_update = int(time()) - 2  # allow some overlap
        for (puzzle, modified) in puzzles:
            puzzle = int(puzzle)
            m_date = strftime("%Y-%m-%d %H:%M:%S", gmtime(modified))
            current_app.logger.info("test {}".format(puzzle))

            (result, col_names) = rowify(
                cur.execute(
                    fetch_query_string("select-all-from-puzzle-by-id.sql"),
                    {"puzzle": puzzle},
                ).fetchall(),
                cur.description,
            )
            if result:
                puzzle_data = result[0]
                r = requests.patch(
                    "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                        HOSTAPI=current_app.config["HOSTAPI"],
                        PORTAPI=current_app.config["PORTAPI"],
                        puzzle_id=puzzle_data["puzzle_id"],
                    ),
                    json={"m_date": m_date,},
                )
                if r.status_code != 200:
                    current_app.logger.warning(
                        "Puzzle details api error. Could not update puzzle m_date to {m_date}. Skipping {puzzle_id}".format(
                            m_date=m_date, puzzle_id=puzzle_data["puzzle_id"],
                        )
                    )
                    continue
                current_app.logger.debug(
                    "Updated puzzle m_date {puzzle_id} {m_date}".format(
                        m_date=m_date, puzzle_id=puzzle_data["puzzle_id"],
                    )
                )
        if len(puzzles) > 0:
            self.log_task()
        cur.close()


class UpdatePlayer(Task):
    "Update the User points, score, m_date from what has recently been put on redis"
    interval = 125
    first_run = True

    def __init__(self, id=None):
        super().__init__(id, __class__.__name__)

    def do_task(self):
        super().do_task()
        made_change = False

        cur = db.cursor()

        user = redis_connection.spop("batchuser")
        while user:
            score = redis_connection.getset(
                "batchscore:{user}".format(user=user), value=0
            )
            redis_connection.expire("batchscore:{user}".format(user=user), DAY)
            points = redis_connection.getset(
                "batchpoints:{user}".format(user=user), value=0
            )
            redis_connection.expire("batchpoints:{user}".format(user=user), DAY)

            current_app.logger.debug(
                "update user {id} with {points} points and score of {score}".format(
                    **{"id": user, "points": points, "score": score}
                )
            )
            # TODO: use newapi/internal/
            cur.execute(
                read_query_file("update_user_points_and_m_date.sql"),
                {
                    "id": user,
                    "points": points,
                    "score": score,
                    "POINTS_CAP": current_app.config["POINTS_CAP"],
                },
            )
            # TODO: use newapi/internal/
            cur.execute(
                read_query_file("update_bit_icon_expiration.sql"), {"user": user}
            )

            user = redis_connection.spop("batchuser")
            db.commit()
            made_change = True

        if self.first_run:
            result = cur.execute(
                read_query_file("select_user_score_and_timestamp.sql")
            ).fetchall()
            if result and len(result):
                current_app.logger.info(
                    "Set rank and timeline on {0} players".format(len(result))
                )
                user_scores = dict(map(lambda x: [x[0], x[1]], result))
                user_timestamps = dict(map(lambda x: [x[0], int(x[2])], result))
                redis_connection.zadd("rank", user_scores)
                redis_connection.zadd("timeline", user_timestamps)
                made_change = True
            self.first_run = False

        if made_change:
            self.log_task()

        cur.close()
        db.commit()


class UpdatePuzzleStats(Task):
    "Update the puzzle stats/timeline from what has recently been put on redis"
    interval = 60
    first_run = True
    last_run = 0

    def __init__(self, id=None):
        super().__init__(id, __class__.__name__)

    def do_task(self):
        super().do_task()
        made_change = False

        cur = db.cursor()

        puzzle = redis_connection.spop("batchpuzzle")
        while puzzle:
            last_batch = redis_connection.zrangebyscore(
                "timeline:{puzzle}".format(puzzle=puzzle),
                self.last_run,
                "+inf",
                withscores=True,
            )
            for (user, update_timestamp) in last_batch:
                current_app.logger.debug(
                    "user: {user}, {update_timestamp}".format(
                        user=user, update_timestamp=update_timestamp
                    )
                )
                user = int(user)
                points = int(
                    redis_connection.getset(
                        "batchpoints:{puzzle}:{user}".format(puzzle=puzzle, user=user),
                        value=0,
                    )
                    or "0"
                )
                redis_connection.expire(
                    "batchpoints:{puzzle}:{user}".format(puzzle=puzzle, user=user), DAY
                )
                if points != 0:
                    result = cur.execute(
                        fetch_query_string("select-all-from-puzzle-by-id.sql"),
                        {"puzzle": puzzle},
                    ).fetchall()
                    if not result:
                        current_app.logger.warn(
                            "no puzzle details found for puzzle {}".format(puzzle)
                        )
                        continue
                    (result, col_names) = rowify(result, cur.description)
                    puzzle_data = result[0]
                    puzzle_id = puzzle_data["puzzle_id"]

                    timestamp = strftime("%Y-%m-%d %H:%M:%S", gmtime(update_timestamp))
                    current_app.logger.debug(
                        "{timestamp} - bumping {points} points on {puzzle} ({puzzle_id}) for player: {player}".format(
                            puzzle=puzzle,
                            puzzle_id=puzzle_id,
                            player=user,
                            points=points,
                            timestamp=timestamp,
                        )
                    )

                    r = requests.post(
                        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/timeline/".format(
                            HOSTAPI=current_app.config["HOSTAPI"],
                            PORTAPI=current_app.config["PORTAPI"],
                            puzzle_id=puzzle_id,
                        ),
                        json={"player": user, "points": points, "timestamp": timestamp},
                    )
                    if r.status_code != 200:
                        current_app.logger.warning(
                            "Puzzle timeline api error. Could not add batchpoints. Skipping {puzzle_id}".format(
                                puzzle_id=puzzle_id,
                            )
                        )
                        continue

                made_change = True
            puzzle = redis_connection.spop("batchpuzzle")

        if self.first_run:
            result = cur.execute(
                read_query_file("get_list_of_puzzles_in_timeline.sql")
            ).fetchall()
            if result and len(result):
                puzzle_list = list(map(lambda x: x[0], result))
                for puzzle in puzzle_list:
                    result = cur.execute(
                        read_query_file(
                            "select_user_score_and_timestamp_per_puzzle.sql"
                        ),
                        {"puzzle": puzzle},
                    ).fetchall()
                    if result and len(result):
                        current_app.logger.info(
                            "Set puzzle ({0}) score and puzzle timeline on {1} players".format(
                                puzzle, len(result)
                            )
                        )
                        user_score = dict(map(lambda x: [x[0], x[1]], result))
                        user_timestamps = dict(map(lambda x: [x[0], int(x[2])], result))
                        redis_connection.zadd(
                            "timeline:{puzzle}".format(puzzle=puzzle), user_timestamps
                        )
                        redis_connection.zadd(
                            "score:{puzzle}".format(puzzle=puzzle), user_score
                        )
                made_change = True

            self.first_run = False

        self.last_run = int(time())

        if made_change:
            self.log_task()

        cur.close()


class UpdatePuzzleQueue(Task):
    "Update puzzle queue for original puzzles (not puzzle instances)"
    interval = MINUTE * 5

    def __init__(self, id=None):
        super().__init__(id, __class__.__name__)

    def do_task(self):
        super().do_task()
        made_change = False

        cur = db.cursor()

        result = cur.execute(
            fetch_query_string("select-active-public-puzzles-due-for-retirement.sql")
        ).fetchall()
        if result:
            for item in result:
                puzzle_id = item[0]
                current_app.logger.debug(
                    "{} has been inactive for more than 7 days".format(puzzle_id)
                )
                r = requests.patch(
                    "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                        HOSTAPI=current_app.config["HOSTAPI"],
                        PORTAPI=current_app.config["PORTAPI"],
                        puzzle_id=puzzle_id,
                    ),
                    json={"status": IN_QUEUE, "queue": QUEUE_INACTIVE},
                )
                if r.status_code != 200:
                    current_app.logger.warning(
                        "Puzzle details api error. Could not update puzzle m_date to {m_date}. Skipping {puzzle_id}".format(
                            m_date=m_date, puzzle_id=puzzle_data["puzzle_id"],
                        )
                    )
                    continue
                made_change = True

        # select all ACTIVE puzzles within each skill range
        skill_range_active_count = 2
        for (low, high) in SKILL_LEVEL_RANGES:
            result = cur.execute(
                read_query_file("count-active-puzzles-within-skill-range.sql"),
                {"low": low, "high": high},
            ).fetchone()
            if result == None or result[0] < skill_range_active_count:
                result = cur.execute(
                    fetch_query_string("select-puzzle-next-in-queue-to-be-active.sql"),
                    {
                        "low": low,
                        "high": high,
                        "active_count": skill_range_active_count,
                    },
                ).fetchall()
                if result:
                    current_app.logger.debug(
                        "Bump next puzzle in queue to be active for skill level range {low}, {high}".format(
                            low=low, high=high
                        )
                    )
                    # TODO: this use to be 4 days in the past, but now using
                    # present time.
                    m_date_now = strftime("%Y-%m-%d %H:%M:%S", gmtime(time()))
                    for item in result:
                        puzzle_id = item[0]
                        current_app.logger.debug(
                            "{} is next in queue to be active".format(puzzle_id)
                        )
                        r = requests.patch(
                            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                                HOSTAPI=current_app.config["HOSTAPI"],
                                PORTAPI=current_app.config["PORTAPI"],
                                puzzle_id=puzzle_id,
                            ),
                            json={"status": ACTIVE, "m_date": m_date_now},
                        )
                        if r.status_code != 200:
                            current_app.logger.warning(
                                "Puzzle details api error. Could not update puzzle m_date to {m_date} and status to active. Skipping {puzzle_id}".format(
                                    m_date=m_date_now,
                                    puzzle_id=puzzle_data["puzzle_id"],
                                )
                            )
                            continue
                        made_change = True

        if made_change:
            self.log_task()

        cur.close()
        db.commit()


class AutoApproveUserNames(Task):
    "Approve user names that have not been approved and have old approved_date."
    interval = 5 * MINUTE

    def __init__(self, id=None):
        super().__init__(id, __class__.__name__)

    def do_task(self):
        super().do_task()

        cur = db.cursor()
        # TODO: use newapi/internal/
        result = cur.execute(
            read_query_file("update-user-name-approved-for-approved_date-due.sql")
        )
        if result.rowcount:
            self.log_task()
        cur.close()
        db.commit()


class SendDigestEmailForAdmin(Task):
    "Let admin know of any items of interest via email"
    interval = DAY

    def __init__(self, id=None):
        super().__init__(id, __class__.__name__)

    def do_task(self):
        super().do_task()

        cur = db.cursor()
        result = cur.execute(
            read_query_file("select-user-name-waiting-to-be-approved.sql")
        ).fetchall()
        if result:
            self.log_task()
            names = []
            (result, col_names) = rowify(result, cur.description)
            for item in result:
                names.append("{approved_date} - {display_name}".format(**item))

            message = "\n".join(names)

            # Send a notification email (silent fail if not configured)
            current_app.logger.debug(message)
            if not current_app.config.get("DEBUG", True):
                try:
                    send_message(
                        current_app.config.get("EMAIL_MODERATOR"),
                        "Puzzle Massive - new names",
                        message,
                        current_app.config,
                    )
                except Exception as err:
                    current_app.logger.warning(
                        "Failed to send notification message. {}".format(err)
                    )
                    pass

        cur.close()
        db.commit()


task_registry = [
    AutoRebuildCompletedPuzzle,
    BumpMinimumDotsForPlayers,
    UpdateModifiedDateOnPuzzle,
    UpdatePlayer,
    UpdatePuzzleStats,
    UpdatePuzzleQueue,
    AutoApproveUserNames,
    SendDigestEmailForAdmin,
]


def all_tasks():
    """
    Cycle through all tasks in the task registry and run them at their set
    interval.
    """

    # Reset scheduler to start by removing any previous scheduled tasks
    redis_connection.delete(scheduler_key)

    now = int(time())
    tasks = {}
    for index in range(len(task_registry)):
        # Create each task with an id corresponding to the index
        tasks[index] = task_registry[index](index)

    task_ids_scheduled_to_now = dict(
        zip(tasks.keys(), map(lambda x: now, range(len(tasks))))
    )

    # reset all tasks to be scheduled now
    redis_connection.zadd(scheduler_key, task_ids_scheduled_to_now)

    while True:
        now = int(time())
        # Get list of tasks on the schedule that are due.
        task_ids = list(map(int, redis_connection.zrangebyscore(scheduler_key, 0, now)))

        # Cycle over each and call the task
        for task_id in task_ids:
            tasks[task_id]()

        sleep(SCHEDULER_INTERVAL)


def main():
    ""
    args = docopt(__doc__)
    config_file = args["--config"]
    task_name = args.get("--task")
    show_list = args.get("--list")

    if task_name:
        OneOffTask = globals().get(task_name)
        if not issubclass(OneOffTask, Task):
            print("{} is not a task in the list".format(task_name))
            return

    if show_list:
        for item in globals():
            Item = globals().get(item)
            if isinstance(Item, type) and issubclass(Item, Task):
                print(item)
        return

    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")

    app = make_app(config=config_file, cookie_secret=cookie_secret)

    with app.app_context():
        # Check if running a one-off, otherwise just run main
        if task_name:
            OneOffTask = globals().get(task_name)
            if issubclass(OneOffTask, Task):
                # Run the task
                oneOffTask = OneOffTask()
                oneOffTask()

        else:
            all_tasks()


if __name__ == "__main__":
    main()
