"""puzzle-massive-testdata - Generate random puzzle data for testing

Usage: puzzle-massive-testdata players [--count=<n>] [--config <file>]
       puzzle-massive-testdata puzzles [--count=<n>] [--pieces=<n>] [--min-pieces=<n>] [--size=<s>] [--config <file>]
       puzzle-massive-testdata instances [--count=<n>] [--pieces=<n>] [--min-pieces=<n>] [--config <file>]
       puzzle-massive-testdata activity [--puzzles=<list>] [--count=<n>] [--config <file>]
       puzzle-massive-testdata --help

Options:
    -h --help         Show this screen.
    --config <file>   Set config file. [default: site.cfg]
    --count=<n>       Create this many items [default: 1]
    --size=<s>        Random image size (passed to imagemagick resize opt) [default: 180x180!]
    --pieces=<n>      Piece count max [default: 9]
    --min-pieces=<n>  Piece count min [default: 0]
    --puzzles=<list>  Comma separated list of puzzle ids

Subcommands:
    players     - Generate some random player data
    puzzles     - Create random images and create puzzles
    instances   - Create instances of existing puzzles for random players
    activity    - Simulate puzzle activity
"""

import sys
import os
import time
from uuid import uuid4
import hashlib
import subprocess
from random import randint, choice, random
import multiprocessing

import requests
from rq import Queue
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
    NEEDS_MODERATION,
    PUBLIC,
    REBUILD,
    RENDERING,
    QUEUE_NEW,
)
from api.database import (
    rowify,
    PUZZLE_CREATE_TABLE_LIST,
    read_query_file,
    generate_new_puzzle_id,
)


QUERY_USER_ID_BY_LOGIN = """
select id from User where ip = :ip and login = :login;
"""


def generate_users(count):
    def generate_name(user_id):
        # TODO: Use generated names from https://www.name-generator.org.uk/
        return "Random Name for " + str(user_id)

    cur = db.cursor()

    for index in range(count):
        ip = ".".join(map(lambda x: str(randint(0, 255)), range(4)))
        score = randint(0, 15000)
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
    for index in range(count):
        link = ""
        description = ""
        bg_color = "#444444"
        permission = PUBLIC
        if min_pieces:
            pieces = randint(min_pieces, max_pieces)
        else:
            pieces = max_pieces
        filename = "random-{}.png".format(str(uuid4()))
        d = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
        puzzle_id = "random-{}".format(
            hashlib.sha224(bytes("%s%s" % (filename, d), "utf-8")).hexdigest()[0:30]
        )

        # Create puzzle dir
        puzzle_dir = os.path.join(current_app.config.get("PUZZLE_RESOURCES"), puzzle_id)
        os.mkdir(puzzle_dir)

        # Create random image
        file_path = os.path.join(puzzle_dir, filename)
        subprocess.check_call(
            ["convert", "-size", "200x150", "plasma:fractal", file_path]
        )
        subprocess.check_call(
            [
                "convert",
                file_path,
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
                os.path.join(puzzle_dir, "original.jpg"),
            ]
        )
        os.unlink(file_path)

        # Insert puzzle directly to render queue instead of setting status to NEEDS_MODERATION
        d = {
            "puzzle_id": puzzle_id,
            "pieces": pieces,
            "name": filename,
            "link": link,
            "description": description,
            "bg_color": bg_color,
            "owner": user,
            "queue": QUEUE_NEW,
            "status": IN_RENDER_QUEUE,
            "permission": permission,
        }
        cur.execute(read_query_file("insert_puzzle.sql"), d)
        db.commit()

        puzzle = rowify(
            cur.execute(
                read_query_file("select_puzzle_id_by_puzzle_id.sql"),
                {"puzzle_id": puzzle_id},
            ).fetchall(),
            cur.description,
        )[0][0]
        puzzle = puzzle["puzzle"]

        cur.execute(
            read_query_file("add-puzzle-file.sql"),
            {
                "puzzle": puzzle,
                "name": "original",
                "url": "/resources/{0}/original.jpg".format(
                    puzzle_id
                ),  # Not a public file (only on admin page)
            },
        )

        cur.execute(
            read_query_file("add-puzzle-file.sql"),
            {
                "puzzle": puzzle,
                "name": "preview_full",
                "url": "/resources/{0}/preview_full.jpg".format(puzzle_id),
            },
        )

        classic_variant = cur.execute(
            read_query_file("select-puzzle-variant-id-for-slug.sql"), {"slug": CLASSIC}
        ).fetchone()[0]
        cur.execute(
            read_query_file("insert-puzzle-instance.sql"),
            {"original": puzzle, "instance": puzzle, "variant": classic_variant},
        )

        db.commit()
        print("pieces: {pieces} {puzzle_id}".format(**locals()))

    puzzles = rowify(
        cur.execute(
            read_query_file("select-puzzles-in-render-queue.sql"),
            {"IN_RENDER_QUEUE": IN_RENDER_QUEUE, "REBUILD": REBUILD},
        ).fetchall(),
        cur.description,
    )[0]
    print("found {0} puzzles to render".format(len(puzzles)))

    # push each puzzle to artist job queue
    for puzzle in puzzles:
        # push puzzle to artist job queue
        job = current_app.createqueue.enqueue_call(
            func="api.jobs.pieceRenderer.render",
            args=([puzzle]),
            result_ttl=0,
            timeout="24h",
        )

    cur.close()


def generate_puzzle_instances(count=1, min_pieces=0, max_pieces=9):

    cur = db.cursor()
    for index in range(count):
        bg_color = "#444444"
        permission = PUBLIC
        if min_pieces:
            pieces = randint(min_pieces, max_pieces)
        else:
            pieces = max_pieces
        result = cur.execute(
            read_query_file("select-random-player-with-available-user-puzzle-slot.sql")
        ).fetchone()[0]
        if result:
            player = result
            # select a random original puzzle

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
                print("no puzzle found")
                continue

            (result, col_names) = rowify(result, cur.description)
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

            db.commit()
            print("pieces: {pieces} {puzzle_id}".format(**locals()))

            job = current_app.createqueue.enqueue_call(
                func="api.jobs.pieceRenderer.render",
                args=([puzzleData]),
                result_ttl=0,
                timeout="24h",
            )
    cur.close()


class UserSession:
    def __init__(self, ip):
        self.ip = ip
        self.headers = {"X-Real-IP": ip}

        self.api_host = "http://localhost:{PORTAPI}".format(
            PORTAPI=current_app.config["PORTAPI"]
        )

        # get test user
        current_user_id = requests.get(
            "{0}/current-user-id/".format(self.api_host), headers=self.headers
        )
        self.shareduser_cookie = current_user_id.cookies["shareduser"]
        self.shareduser = int(current_user_id.content)

    def get_data(self, route):
        r = requests.get(
            "".join([self.api_host, route]),
            cookies={"shareduser": self.shareduser_cookie},
            headers=self.headers,
        )
        if r.status_code in (429, 409):
            try:
                data = r.json()
            except ValueError as err:
                time.sleep(1)
                print(r.text)
                return
            print(data.get("msg"))
            if data.get("timeout"):
                time.sleep(data.get("timeout", 1))
            return
        try:
            data = r.json()
        except ValueError as err:
            print("ERROR reading json: {}".format(err))
            print(r.text)
            return
        if r.status_code >= 400:
            print(
                "ERROR: {status_code} {url}".format(
                    status_code=r.status_code, url=r.url
                )
            )
            return
        return data

    def patch_data(self, route, payload={}, headers={}):
        my_headers = self.headers.copy()
        my_headers.update(headers)
        r = requests.patch(
            "".join([self.api_host, route]),
            data=payload,
            cookies={"shareduser": self.shareduser_cookie},
            headers=my_headers,
        )

        if r.status_code in (429, 409):
            try:
                data = r.json()
            except ValueError as err:
                time.sleep(1)
                print(r.text)
                return
            print(data.get("msg"))
            if data.get("timeout"):
                time.sleep(data.get("timeout", 1))
            return
        try:
            data = r.json()
        except ValueError as err:
            print("ERROR reading json: {}".format(err))
            print(r.text)
            return
        if r.status_code >= 400:
            print(
                "ERROR: {status_code} {url}".format(
                    status_code=r.status_code, url=r.url
                )
            )
            if r.status_code == 429:
                timeout = data.get("timeout")
                if timeout:
                    print("timeout {}".format(timeout))
                    time.sleep(timeout)
                return
            return
        return data


class PuzzlePieces:
    def __init__(self, user_session, puzzle, puzzle_id, table_width, table_height):
        self.user_session = user_session
        self.puzzle = puzzle
        self.puzzle_id = puzzle_id
        self.puzzle_pieces = self.user_session.get_data(
            "/puzzle-pieces/{0}/".format(self.puzzle_id)
        )
        self.table_width = table_width
        self.table_height = table_height
        self.movable_pieces = [
            x["id"] for x in self.puzzle_pieces["positions"] if x["s"] is not "1"
        ]
        # TODO: connect to the stream and update movable_pieces

    def move_random_pieces_with_delay(self, delay=1, max_delay=10):
        while True:
            random_delay = round((random() * (max_delay - delay)), 3) + delay
            self.move_random_piece()
            time.sleep(random_delay)

    def move_random_piece(self):
        piece_id = choice(self.movable_pieces)
        x = randint(0, self.table_width - 100)
        y = randint(0, self.table_height - 100)
        piece_token = self.user_session.get_data(
            "/puzzle/{puzzle_id}/piece/{piece_id}/token/?mark={mark}".format(
                puzzle_id=self.puzzle_id,
                piece_id=piece_id,
                mark=self.puzzle_pieces["mark"],
            )
        )
        if piece_token and piece_token.get("token"):
            puzzle_pieces_move = self.user_session.patch_data(
                "/puzzle/{puzzle_id}/piece/{piece_id}/move/".format(
                    puzzle_id=self.puzzle_id, piece_id=piece_id
                ),
                payload={"x": x, "y": y},
                headers={"Token": piece_token["token"]},
            )
            if puzzle_pieces_move:
                if puzzle_pieces_move.get("msg") == "boing":
                    raise Exception("boing")
                # Reset karma:puzzle:ip redis key when it gets low
                if puzzle_pieces_move["karma"] < 2:
                    print("resetting karma for {ip}".format(ip=self.user_session.ip))
                    karma_key = init_karma_key(
                        redis_connection, self.puzzle, self.user_session.ip
                    )
                    redis_connection.delete(karma_key)


class PuzzleActivityJob:
    def __init__(self, puzzle_id, ip):
        self.puzzle_id = puzzle_id
        self.ip = ip
        cur = db.cursor()
        result = cur.execute(
            "select id, table_width, table_height from Puzzle where puzzle_id = :puzzle_id;",
            {"puzzle_id": self.puzzle_id},
        ).fetchall()
        (result, col_names) = rowify(result, cur.description)
        self.puzzle_details = result[0]
        cur.close()

    def run(self):
        user_session = UserSession(ip=self.ip)
        puzzle_pieces = PuzzlePieces(
            user_session,
            self.puzzle_details["id"],
            self.puzzle_id,
            self.puzzle_details["table_width"],
            self.puzzle_details["table_height"],
        )
        puzzle_pieces.move_random_pieces_with_delay(delay=1, max_delay=10)


def simulate_puzzle_activity(puzzle_ids, count=1):
    """

    """

    user_session = UserSession(ip="127.0.0.1")

    gallery_puzzle_list = user_session.get_data("/gallery-puzzle-list/")

    listed_puzzle_ids = [x["puzzle_id"] for x in gallery_puzzle_list["puzzles"]]
    _puzzle_ids = puzzle_ids or listed_puzzle_ids
    cur = db.cursor()
    result = cur.execute(
        "select distinct ip from User order by score desc limit :count;",
        {"count": int(count * len(_puzzle_ids))},
    ).fetchall()
    if not result:
        print("Add players first")
        return
    players = [x[0] for x in result]
    cur.close()

    jobs = []
    while players:
        for puzzle_id in puzzle_ids or listed_puzzle_ids:
            ip = players.pop()
            puzzle_activity_job = PuzzleActivityJob(puzzle_id, ip)
            jobs.append(multiprocessing.Process(target=puzzle_activity_job.run))
            if not players:
                break

    for job in jobs:
        job.start()

    for job in jobs:
        job.join()


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

    app = make_app(
        config=config_file, cookie_secret=cookie_secret, database_writable=True
    )

    with app.app_context():
        if args.get("players"):
            print("Creating {} players".format(count))
            generate_users(count)

        elif args.get("puzzles"):
            print(
                "Creating {count} puzzles at {size} with up to {max_pieces} pieces".format(
                    count=count, size=size, max_pieces=max_pieces, min_pieces=min_pieces
                )
            )
            generate_puzzles(
                count=count, size=size, min_pieces=min_pieces, max_pieces=max_pieces
            )

        elif args.get("instances"):
            print(
                "Creating {count} puzzle instances with up to {max_pieces} pieces".format(
                    count=count, max_pieces=max_pieces, min_pieces=min_pieces
                )
            )
            generate_puzzle_instances(
                count=count, min_pieces=min_pieces, max_pieces=max_pieces
            )

        elif args.get("activity"):
            print("Simulating puzzle activity")
            puzzle_ids = []
            if puzzles:
                puzzle_ids = puzzles.split(",")
            simulate_puzzle_activity(puzzle_ids, count=count)


if __name__ == "__main__":
    main()
