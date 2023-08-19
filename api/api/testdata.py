"""puzzle-massive-testdata - Generate random puzzle data for testing

Usage: puzzle-massive-testdata players [--count=<n>] [--config <file>]
       puzzle-massive-testdata puzzles [--count=<n>] [--pieces=<n>] [--min-pieces=<n>] [--size=<s>] [--config <file>]
       puzzle-massive-testdata instances [--count=<n>] [--pieces=<n>] [--min-pieces=<n>] [--config <file>]
       puzzle-massive-testdata activity [--puzzles=<list>] [--count=<n>] [--delay=<f>] [--config <file>] [--internal]
       puzzle-massive-testdata --help

Options:
    -h --help         Show this screen.
    --config <file>   Set config file. [default: site.cfg]
    --count=<n>       Create this many items [default: 1]
    --size=<s>        Random image size (passed to imagemagick resize opt) [default: 180x180!]
    --pieces=<n>      Piece count max [default: 9]
    --min-pieces=<n>  Piece count min [default: 0]
    --puzzles=<list>  Comma separated list of puzzle ids
    --delay=<n>       Max delay in seconds [default: 0.1]
    --internal        Use internal piece move which don't use rules

Subcommands:
    players     - Generate some random player data
    puzzles     - Create random images and create puzzles
    instances   - Create instances of existing puzzles for random players
    activity    - Simulate puzzle activity
"""

import os
import time
from uuid import uuid4
import hashlib
import subprocess
from random import randint, choice, random
import multiprocessing
from logging.config import dictConfig
from tempfile import NamedTemporaryFile

import requests
from docopt import docopt
from flask import current_app

from api.app import db, redis_connection, make_app
from api.tools import loadConfig, init_karma_key
from api.user import generate_user_login
from api.constants import (
    ACTIVE,
    CLASSIC,
    COMPLETED,
    FROZEN,
    IN_QUEUE,
    IN_RENDER_QUEUE,
    PUBLIC,
    REBUILD,
    RENDERING,
    QUEUE_NEW,
)
from api.database import (
    rowify,
    read_query_file,
)


QUERY_USER_ID_BY_LOGIN = """
select id from User where ip = :ip and login = :login;
"""


def generate_users(count):
    def generate_name(user_id):
        # TODO: Use generated names from https://www.name-generator.org.uk/
        return "Random Name for " + str(user_id)

    for index in range(count):
        cur = db.cursor()
        ip = ".".join(map(lambda x: str(randint(0, 255)), range(4)))
        # The score is more likely to be 0 since most players are new
        score = randint(0, 15000) if choice(range(0, 15)) == 0 else 0
        login = generate_user_login()
        query = """insert into User (points, score, login, m_date, ip) values
                (:points, :score, :login, datetime('now'), :ip)"""
        cur.execute(
            query,
            {
                "ip": ip,
                "login": login,
                "points": current_app.config["NEW_USER_STARTING_POINTS"],
                "score": score,
            },
        )
        result = cur.execute(
            QUERY_USER_ID_BY_LOGIN, {"ip": ip, "login": login}
        ).fetchall()
        (result, col_names) = rowify(result, cur.description)
        user_id = result[0]["id"]

        # Claim a random bit icon
        cur.execute(read_query_file("claim_random_bit_icon.sql"), {"user": user_id})

        # Randomly Add slots
        for chance in range(randint(0, 1)):
            slotcount = randint(1, 6)
            if slotcount == 6:
                slotcount = randint(1, 50)
            if slotcount == 50:
                slotcount = randint(50, 250)
            for slot in range(slotcount):
                cur.execute(
                    read_query_file("add-new-user-puzzle-slot.sql"), {"player": user_id}
                )

        # Randomly assign player names
        chance_for_name = randint(0, 5)
        if chance_for_name == 5:
            display_name = generate_name(user_id)
            name = display_name.lower()
            cur.execute(
                read_query_file(
                    "add-user-name-on-name-register-for-player-to-be-reviewed.sql"
                ),
                {
                    "player_id": user_id,
                    "name": name,
                    "display_name": display_name,
                    "time": "+{} minutes".format(randint(1, 60)),
                },
            )

        cur.close()
        db.commit()


def generate_puzzles(count=1, size="180x180!", min_pieces=0, max_pieces=9, user=3):

    cur = db.cursor()
    result = cur.execute(
        "select ip from User where id = :user;", {"user": user}
    ).fetchone()
    cur.close()
    if not result:
        current_app.logger.warn("No player with that id")
        return

    user_session = UserSession(ip=result[0])

    for index in range(count):
        link = ""
        description = ""
        bg_color = "#444444"
        permission = PUBLIC
        if min_pieces:
            pieces = randint(min_pieces, max_pieces)
        else:
            pieces = max_pieces

        # Create random image
        random_image_file = NamedTemporaryFile(suffix=".jpg", delete=False)
        file_path = random_image_file.name
        random_image_file.close()
        w = randint(200, 1000)
        h = randint(200, 1000)
        subprocess.run(
            [
                "convert",
                "-size",
                f"{w}x{h}",
                "-format",
                "png",
                "plasma:fractal",
                file_path,
            ]
        )
        subprocess.run(
            [
                "mogrify",
                "-paint",
                "10",
                "-blur",
                "0x5",
                "-paint",
                "10",
                "-filter",
                "box",
                "-resize",
                size,
                "+repage",
                "-auto-level",
                "-quality",
                "85%",
                "-format",
                "jpg",
                file_path,
            ]
        )
        fp = open(file_path, mode="rb")

        user_session.post_data(
            route="/puzzle-upload/",
            host="api",
            payload={
                "features": [],
                "contributor": current_app.config.get("NEW_PUZZLE_CONTRIB"),
                "pieces": pieces,
                "bg_color": bg_color,
                "permission": permission,
                "description": description,
                "link": link,
            },
            files={"upload_file": fp},
        )
        time.sleep(1)
        fp.close()
        os.unlink(file_path)
        current_app.logger.info(
            f"{pieces} piece puzzle with size {size} and plasma:fractal {w}x{h} submitted for moderation"
        )


def generate_puzzle_instances(count=1, min_pieces=0, max_pieces=9):

    for index in range(count):
        bg_color = "#444444"
        permission = PUBLIC
        if min_pieces:
            pieces = randint(min_pieces, max_pieces)
        else:
            pieces = max_pieces
        cur = db.cursor()
        result = cur.execute(
            read_query_file("select-random-player-with-available-user-puzzle-slot.sql")
        ).fetchone()[0]
        cur.close()
        if result:
            player = result
            # select a random original puzzle

            cur = db.cursor()
            result = cur.execute(
                read_query_file("select-random-puzzle-for-new-puzzle-instance.sql"),
                {
                    "ACTIVE": ACTIVE,
                    "IN_QUEUE": IN_QUEUE,
                    "COMPLETED": COMPLETED,
                    "FROZEN": FROZEN,
                    "REBUILD": REBUILD,
                    "IN_RENDER_QUEUE": IN_RENDER_QUEUE,
                    "RENDERING": RENDERING,
                    "PUBLIC": PUBLIC,
                },
            ).fetchall()
            if not result:
                current_app.logger.warn("no puzzle found")
                cur.close()
                continue

            (result, col_names) = rowify(result, cur.description)
            cur.close()
            originalPuzzleData = result[0]

            filename = "random-{}.png".format(str(uuid4()))
            d = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
            puzzle_id = "rnd-instance-{}".format(
                hashlib.sha224(bytes("%s%s" % (filename, d), "utf-8")).hexdigest()[0:30]
            )

            # Create puzzle dir
            puzzle_dir = os.path.join(
                current_app.config.get("PUZZLE_RESOURCES"), puzzle_id
            )
            os.mkdir(puzzle_dir)

            # Insert puzzle directly to render queue
            d = {
                "puzzle_id": puzzle_id,
                "pieces": pieces,
                "name": originalPuzzleData["name"],
                "link": originalPuzzleData["link"],
                "description": originalPuzzleData["description"],
                "bg_color": bg_color,
                "owner": player,
                "queue": QUEUE_NEW,
                "status": IN_RENDER_QUEUE,
                "permission": permission,
            }
            cur = db.cursor()
            cur.execute(
                """insert into Puzzle (
            puzzle_id,
            pieces,
            name,
            link,
            description,
            bg_color,
            owner,
            queue,
            status,
            permission) values
            (:puzzle_id,
            :pieces,
            :name,
            :link,
            :description,
            :bg_color,
            :owner,
            :queue,
            :status,
            :permission);
            """,
                d,
            )
            db.commit()

            result = cur.execute(
                "select * from Puzzle where puzzle_id = :puzzle_id;",
                {"puzzle_id": puzzle_id},
            ).fetchall()
            if not result:
                cur.close()
                raise Exception("no puzzle instance")

            (result, col_names) = rowify(result, cur.description)
            puzzleData = result[0]
            puzzle = puzzleData["id"]

            classic_variant = cur.execute(
                read_query_file("select-puzzle-variant-id-for-slug.sql"),
                {"slug": CLASSIC},
            ).fetchone()[0]
            cur.execute(
                read_query_file("insert-puzzle-instance.sql"),
                {
                    "original": originalPuzzleData["id"],
                    "instance": puzzle,
                    "variant": classic_variant,
                },
            )

            cur.execute(
                read_query_file("fill-user-puzzle-slot.sql"),
                {"player": player, "puzzle": puzzle},
            )
            cur.close()

            db.commit()
            current_app.logger.info("pieces: {pieces} {puzzle_id}".format(**locals()))

            job = current_app.createqueue.enqueue(
                "api.jobs.pieceRenderer.render",
                [puzzleData],
                result_ttl=0,
                job_timeout="24h",
            )


class UserSession:
    def __init__(self, ip):
        self.ip = ip
        self.headers = {"X-Real-IP": ip}

        self.api_host = "http://{HOSTAPI}:{PORTAPI}".format(
            HOSTAPI=current_app.config["HOSTAPI"], PORTAPI=current_app.config["PORTAPI"]
        )
        self.publish_host = "http://{HOSTPUBLISH}:{PORTPUBLISH}".format(
            HOSTPUBLISH=current_app.config["HOSTPUBLISH"],
            PORTPUBLISH=current_app.config["PORTPUBLISH"],
        )

        cur = db.cursor()
        result = cur.execute(
            read_query_file("select-user-id-by-ip-and-no-password.sql"), {"ip": ip}
        ).fetchall()
        if result:
            (result, col_names) = rowify(result, cur.description)
            shareduser = result[0]["id"]
            redis_connection.zrem("bannedusers", shareduser)
        cur.close()

        # get test user
        current_user_id = requests.get(
            "{0}/current-user-id/".format(self.api_host), headers=self.headers
        )
        # print('ip {} and {}'.format(ip, current_user_id.cookies))
        self.shareduser_cookie = current_user_id.cookies["shareduser"]
        self.shareduser = int(current_user_id.content)

    def get_data(self, route, host):
        if host == "api":
            _host = self.api_host
        elif host == "publish":
            _host = self.publish_host

        r = requests.get(
            "".join([_host, route]),
            cookies={"shareduser": self.shareduser_cookie},
            headers=self.headers,
        )
        if r.status_code in (429, 409):
            try:
                data = r.json()
            except ValueError as err:
                current_app.logger.debug(err)
                time.sleep(1)
                current_app.logger.debug(r.text)
                return
            # print(data.get("msg"))
            if data.get("timeout"):
                # time.sleep(data.get("timeout", 1))
                time.sleep(1)
                raise Exception(data.get("type"))
            return
        data = {}
        if r.status_code >= 400:
            # current_app.logger.debug(
            #     "ERROR get: {status_code} {url}".format(
            #         status_code=r.status_code, url=r.url
            #     )
            # )
            return
        if r.status_code >= 200:
            try:
                data = r.json()
            except ValueError as err:
                current_app.logger.debug("ERROR reading json: {}".format(err))
                current_app.logger.debug(r.text)
                return
        return data

    def patch_data(self, route, host, payload={}, headers={}):
        if host == "api":
            _host = self.api_host
        elif host == "publish":
            _host = self.publish_host

        my_headers = self.headers.copy()
        my_headers.update(headers)
        r = requests.patch(
            "".join([_host, route]),
            json=payload,
            cookies={"shareduser": self.shareduser_cookie},
            headers=my_headers,
        )

        data = {}
        if r.status_code in (429, 409):
            try:
                data = r.json()
            except ValueError as err:
                current_app.logger.debug(err)
                time.sleep(1)
                current_app.logger.debug(r.text)
                return
            # print(data.get("msg"))
            if data.get("timeout"):
                # time.sleep(data.get("timeout", 1))
                raise Exception("timeout")
            return
        if r.status_code == 503:
            data = r.json()
            raise Exception("too_active")
        if r.status_code == 204:
            return
        if r.status_code >= 400:
            current_app.logger.debug(payload)
            try:
                data = r.json()
                current_app.logger.debug(data)
            except ValueError as err:
                current_app.logger.debug(err)
                current_app.logger.debug(r.text)
            current_app.logger.debug(
                "ERROR patch: {status_code} {url}".format(
                    status_code=r.status_code, url=r.url
                )
            )
            if r.status_code == 429:
                timeout = data.get("timeout")
                if timeout:
                    current_app.logger.debug("timeout {}".format(timeout))
                    time.sleep(timeout)
                return
            if r.status_code == 400:
                raise Exception("fail")
            return
        if r.status_code >= 200:
            try:
                data = r.json()
            except ValueError as err:
                current_app.logger.debug("ERROR reading json: {}".format(err))
                current_app.logger.debug(r.text)
                return
        return data

    def post_data(self, route, host, payload={}, headers={}, files={}):
        if host == "api":
            _host = self.api_host
        elif host == "publish":
            _host = self.publish_host

        my_headers = self.headers.copy()
        my_headers.update(headers)
        r = requests.post(
            "".join([_host, route]),
            data=payload,
            files=files,
            cookies={"shareduser": self.shareduser_cookie},
            headers=my_headers,
            allow_redirects=False,
        )

        data = {}
        if r.status_code in (429, 409):
            try:
                data = r.json()
            except ValueError as err:
                current_app.logger.debug(err)
                time.sleep(1)
                current_app.logger.debug(r.text)
                return
            # print(data.get("msg"))
            if data.get("timeout"):
                # time.sleep(data.get("timeout", 1))
                raise Exception("timeout")
            return
        if r.status_code == 503:
            data = r.json()
            raise Exception("too_active")
        if r.status_code == 204:
            return
        if r.status_code >= 400:
            current_app.logger.debug(
                "ERROR post: {status_code} {url}".format(
                    status_code=r.status_code, url=r.url
                )
            )
            if r.status_code == 429:
                timeout = data.get("timeout")
                if timeout:
                    current_app.logger.debug("timeout {}".format(timeout))
                    time.sleep(timeout)
                return
            return
        return data


class PuzzlePieces:
    def __init__(self, user_sessions, puzzle, puzzle_id, table_width, table_height):
        self.user_sessions = user_sessions
        self.puzzle = puzzle
        self.puzzle_id = puzzle_id

        for user_session in self.user_sessions:
            karma_key = init_karma_key(
                redis_connection, self.puzzle, user_session.ip, current_app.config
            )
            redis_connection.delete(karma_key)

        self.puzzle_pieces = self.user_sessions[0].get_data(
            "/puzzle-pieces/{0}/".format(self.puzzle_id), "api"
        )
        self.mark = uuid4().hex[:10]
        self.table_width = table_width
        self.table_height = table_height
        self.movable_pieces = [
            x["id"] for x in self.puzzle_pieces["positions"] if x.get("s") != "1"
        ]
        # TODO: connect to the stream and update movable_pieces

    def move_random_pieces_with_delay(
        self, delay=1, max_delay=10, internal_piece_move=False
    ):
        while True:
            random_delay = round((random() * (max_delay - delay)), 3) + delay
            for user_session in self.user_sessions:
                if internal_piece_move:
                    self.internal_move_random_piece(user_session)
                else:
                    self.move_random_piece(user_session)
                time.sleep(random_delay / len(self.user_sessions))

    def internal_move_random_piece(self, user_session):
        piece_id = choice(self.movable_pieces)
        if piece_id is False:
            return
        x = randint(0, self.table_width - 100)
        y = randint(0, self.table_height - 100)
        start = time.perf_counter()

        try:
            user_session.patch_data(
                "/internal/puzzle/{puzzle_id}/piece/{piece_id}/move/".format(
                    puzzle_id=self.puzzle_id, piece_id=piece_id
                ),
                "publish",
                payload={"x": x, "y": y, "r": 0},
            )
        except Exception as err:
            if str(err) == "too_active":
                redis_connection.incr("testdata:too_active")
                time.sleep(30)
            elif str(err) == "fail":
                # Stop trying to move this piece if failed for any 400 type errors
                try:
                    # Need to keep the same rate of piece movements so maintain
                    # the size of the list.
                    self.movable_pieces.remove(piece_id)
                    self.movable_pieces.append(False)
                except ValueError:
                    pass
            return

        end = time.perf_counter()
        duration = end - start
        redis_connection.rpush("testdata:pa", duration)

    def move_random_piece(self, user_session):
        piece_id = choice(self.movable_pieces)
        if piece_id is False:
            return
        x = randint(0, self.table_width - 100)
        y = randint(0, self.table_height - 100)
        start = time.perf_counter()
        piece_token = None
        try:
            piece_token = user_session.get_data(
                "/puzzle/{puzzle_id}/piece/{piece_id}/token/?mark={mark}".format(
                    puzzle_id=self.puzzle_id,
                    piece_id=piece_id,
                    mark=self.mark,
                ),
                "publish",
            )
        except Exception as err:
            # ("resetting karma for {ip}".format(ip=user_session.ip))
            karma_key = init_karma_key(
                redis_connection, self.puzzle, user_session.ip, current_app.config
            )
            redis_connection.delete(karma_key)
            redis_connection.zrem("bannedusers", user_session.shareduser)
            # current_app.logger.debug(f"get token error: {err}")
            if str(err) == "blockedplayer":
                blockedplayers_for_puzzle_key = "blockedplayers:{puzzle}".format(
                    puzzle=self.puzzle
                )
                # current_app.logger.debug("clear out {}".format(blockedplayers_for_puzzle_key))
                redis_connection.delete(blockedplayers_for_puzzle_key)
            return

        if piece_token and piece_token.get("token"):
            puzzle_pieces_move = None
            try:
                puzzle_pieces_move = user_session.patch_data(
                    "/puzzle/{puzzle_id}/piece/{piece_id}/move/".format(
                        puzzle_id=self.puzzle_id, piece_id=piece_id
                    ),
                    "publish",
                    payload={"x": x, "y": y, "r": 0},
                    headers={"Token": piece_token["token"], "Mark": self.mark},
                )
            except Exception as err:
                if str(err) == "too_active":
                    redis_connection.incr("testdata:too_active")
                    time.sleep(30)
                elif str(err) == "fail":
                    # Stop trying to move this piece if failed for any 400 type errors
                    try:
                        # Need to keep the same rate of piece movements so maintain
                        # the size of the list.
                        self.movable_pieces.remove(piece_id)
                        self.movable_pieces.append(False)
                    except ValueError:
                        pass
                else:
                    # current_app.logger.debug('move exception {}'.format(err))
                    # current_app.logger.debug("resetting karma for {ip}".format(ip=user_session.ip))
                    karma_key = init_karma_key(
                        redis_connection,
                        self.puzzle,
                        user_session.ip,
                        current_app.config,
                    )
                    redis_connection.delete(karma_key)
                    redis_connection.zrem("bannedusers", user_session.shareduser)
                return
            if puzzle_pieces_move:
                if puzzle_pieces_move.get("msg") == "boing":
                    raise Exception("boing")
                # Reset karma:puzzle:ip redis key when it gets low
                if puzzle_pieces_move["karma"] < 2:
                    # print("resetting karma for {ip}".format(ip=user_session.ip))
                    karma_key = init_karma_key(
                        redis_connection,
                        self.puzzle,
                        user_session.ip,
                        current_app.config,
                    )
                    redis_connection.delete(karma_key)
            else:
                # empty response (204) means success
                end = time.perf_counter()
                duration = end - start
                redis_connection.rpush("testdata:pa", duration)


class PuzzleActivityJobStats:
    def run(self):
        interval = 30
        key_list = [
            "testdata:pa",
            "testdata:token",
            "testdata:publish",
            "testdata:translate",
            "testdata:move",
        ]
        for key in key_list:
            redis_connection.delete(key)
        while True:
            for key in key_list:
                duration_list = redis_connection.lrange(key, 0, -1)
                duration_list_count = len(duration_list)
                redis_connection.ltrim(key, duration_list_count, -1)
                if duration_list_count:
                    avg = sum(map(float, duration_list)) / float(duration_list_count)
                    piece_moves_per_second = duration_list_count / interval
                    current_app.logger.info(
                        f"""
{key}
count: {duration_list_count}
per second: {piece_moves_per_second}
average latency: {avg}"""
                    )
            too_active_count = int(redis_connection.get("testdata:too_active") or "0")
            if too_active_count:
                current_app.logger.info(
                    "too active error count: {}".format(too_active_count)
                )
                redis_connection.decr("testdata:too_active", amount=too_active_count)
            time.sleep(interval)


class PuzzleActivityJob:
    def __init__(self, puzzle_id, ips, max_delay=0.1, internal_piece_move=False):
        self.puzzle_id = puzzle_id
        self.ips = ips
        self.max_delay = max_delay
        self.internal_piece_move = internal_piece_move
        self.user_sessions = list(map(lambda ip: UserSession(ip=ip), self.ips))
        cur = db.cursor()
        result = cur.execute(
            "select id, table_width, table_height from Puzzle where puzzle_id = :puzzle_id;",
            {"puzzle_id": self.puzzle_id},
        ).fetchall()
        (result, col_names) = rowify(result, cur.description)
        self.puzzle_details = result[0]
        cur.close()
        redis_connection.delete("testdata:too_active")

    def run(self):
        puzzle_pieces = PuzzlePieces(
            self.user_sessions,
            self.puzzle_details["id"],
            self.puzzle_id,
            self.puzzle_details["table_width"],
            self.puzzle_details["table_height"],
        )
        puzzle_pieces.move_random_pieces_with_delay(
            delay=0.1,
            max_delay=self.max_delay,
            internal_piece_move=self.internal_piece_move,
        )


def simulate_puzzle_activity(puzzle_ids, count=1, max_delay=0.1, internal=False):
    """"""
    cur = db.cursor()
    result = cur.execute(
        "select distinct ip from User order by random() limit 1;",
    ).fetchone()
    cur.close()
    if not result:
        current_app.logger.warn("Add players first")
        return

    user_session = UserSession(ip=result[0])

    _puzzle_ids = puzzle_ids

    jobs = []
    puzzle_activity_job_stats = PuzzleActivityJobStats()
    jobs.append(multiprocessing.Process(target=puzzle_activity_job_stats.run))

    for i, puzzle_id in enumerate(_puzzle_ids):
        cur = db.cursor()
        result = cur.execute(
            "select distinct ip from User order by id desc limit :count offset :offset_amount;",
            {"count": int(count), "offset_amount": int(count) * i},
        ).fetchall()
        cur.close()
        if not result:
            current_app.logger.warning("Add players first")
            continue
        players = [x[0] for x in result]
        puzzle_activity_job = PuzzleActivityJob(
            puzzle_id, players, max_delay=max_delay, internal_piece_move=internal
        )
        jobs.append(multiprocessing.Process(target=puzzle_activity_job.run))

    for job in jobs:
        job.start()

    for job in jobs:
        job.join()
        time.sleep(0.1)


def main():
    args = docopt(__doc__, version="0.0")

    config_file = args["--config"]
    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")

    count = int(args.get("--count"))
    size = args.get("--size")
    max_pieces = int(args.get("--pieces"))
    min_pieces = int(args.get("--min-pieces"))
    puzzles = args.get("--puzzles")
    delay = float(args.get("--delay"))
    internal = args.get("--internal")

    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://flask.logging.wsgi_errors_stream",
                    "formatter": "default",
                }
            },
            "root": {"level": "INFO", "handlers": ["wsgi"]},
        }
    )
    app = make_app(
        config=config_file,
        cookie_secret=cookie_secret,
        database_writable=True,
        DEBUG=False,
    )

    with app.app_context():
        if args.get("players"):
            current_app.logger.info("Creating {} players".format(count))
            generate_users(count)

        elif args.get("puzzles"):
            current_app.logger.info(
                f"Creating {count} puzzles at {size} with up to {max_pieces} pieces"
            )
            generate_puzzles(
                count=count, size=size, min_pieces=min_pieces, max_pieces=max_pieces
            )

        elif args.get("instances"):
            current_app.logger.info(
                f"Creating {count} puzzle instances with up to {max_pieces} pieces"
            )
            generate_puzzle_instances(
                count=count, min_pieces=min_pieces, max_pieces=max_pieces
            )

        elif args.get("activity"):
            current_app.logger.info("Simulating puzzle activity")
            puzzle_ids = []
            if puzzles:
                puzzle_ids = puzzles.split(",")
            simulate_puzzle_activity(
                puzzle_ids, count=count, max_delay=delay, internal=internal
            )


if __name__ == "__main__":
    main()
