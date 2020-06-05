"""convertPiecesToDB.py

Usage: convertPiecesToDB.py [--config <file>] [--cleanup]
       convertPiecesToDB.py --help

Options:
  -h --help         Show this screen.
  --config <file>   Set config file. [default: site.cfg]
  --cleanup         Clear redis data after transferring it to DB
"""
from __future__ import print_function

# This job should be ran by a janitor worker.  It should find all puzzles in
# redis that haven't had any activity in the last week or so.

import sys
import os.path
import math
import time
from docopt import docopt

from flask import current_app

import requests

from api.app import redis_connection, db, make_app
from api.database import rowify, read_query_file
from api.tools import loadConfig, deletePieceDataFromRedis
from api.constants import MAINTENANCE


def transfer(puzzle, cleanup=True):
    """
    Transfer the puzzle data from Redis to the database. If the cleanup flag is
    set the Redis data for the puzzle will be removed afterward.
    """
    current_app.logger.info("transferring puzzle: {0}".format(puzzle))
    cur = db.cursor()

    query = """select * from Puzzle where (id = :puzzle)"""
    (result, col_names) = rowify(
        cur.execute(query, {"puzzle": puzzle}).fetchall(), cur.description
    )
    if not result:
        # Most likely because of a database switch and forgot to run this script
        # between those actions.
        # TODO: Raise an error here and let the caller decide how to handle it.
        current_app.logger.warning(
            "Puzzle {} not in database. Skipping.".format(puzzle)
        )
        return

    puzzle_data = result[0]

    puzzle_previous_status = puzzle_data["status"]
    r = requests.patch(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle_data["puzzle_id"],
        ),
        json={"status": MAINTENANCE,},
    )
    current_app.logger.debug(r.status_code)
    if r.status_code != 200:
        # TODO: Raise an error here and let the caller decide how to handle it.
        current_app.logger.warning(
            "Puzzle details api error when setting status to maintenance {}".format(
                puzzle_data["puzzle_id"]
            )
        )
        return

    (all_pieces, col_names) = rowify(
        cur.execute(
            read_query_file("select_all_piece_props_for_puzzle.sql"), {"puzzle": puzzle}
        ).fetchall(),
        cur.description,
    )

    query_update_piece = read_query_file("update_piece_props_for_puzzle.sql")

    # Save the redis data to the db if it has changed
    for piece in all_pieces:
        has_changes = False
        pieceFromRedis = redis_connection.hgetall(
            "pc:{puzzle}:{id}".format(puzzle=puzzle, id=piece["id"])
        )

        # The redis data may be empty so skip updating the db
        if len(pieceFromRedis) == 0:
            continue

        # Compare redis data with db for any changes
        for (prop, colname) in [
            ("x", "x"),
            ("y", "y"),
            ("r", "r"),
            ("g", "parent"),
            ("s", "status"),
        ]:
            redis_piece_prop = pieceFromRedis.get(prop)
            redis_piece_prop = (
                int(redis_piece_prop)
                if isinstance(redis_piece_prop, str)
                else redis_piece_prop
            )
            if redis_piece_prop != piece[colname]:
                current_app.logger.debug(
                    "{} has {} changes. {} != {}".format(
                        piece["id"], colname, redis_piece_prop, piece[colname]
                    )
                )
                piece[colname] = redis_piece_prop
                has_changes = True

        if has_changes:
            # TODO: use newapi/internal/
            cur.execute(query_update_piece, piece)

    if cleanup:
        deletePieceDataFromRedis(redis_connection, puzzle, all_pieces)

    db.commit()
    cur.close()

    r = requests.patch(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle_data["puzzle_id"],
        ),
        json={"status": puzzle_previous_status,},
    )
    current_app.logger.debug(r.status_code)
    if r.status_code != 200:
        # TODO: Raise an error here and let the caller decide how to handle it.
        current_app.logger.warning("Puzzle details api error")
        return


def transferOldest(target_memory):

    # No puzzles that have been modified in the last 30 minutes
    newest = int(time.time()) - (30 * 60)

    # Get the 10 oldest puzzles
    puzzles = redis_connection.zrange("pcupdates", 0, 10, withscores=True)
    # print('cycle over old puzzles: {0}'.format(puzzles))
    for (puzzle, timestamp) in puzzles:
        # There may be a chance that since this process has started that
        # a puzzle could have been updated.
        latest_timestamp = redis_connection.zscore("pcupdates", puzzle)

        if latest_timestamp < newest:
            # print('transfer: {0}'.format(puzzle))
            transfer(puzzle)
            memory = redis_connection.info(section="memory")
            # print('used_memory: {used_memory_human}'.format(**memory))
            if memory.get("used_memory") < target_memory:
                break


def transferAll(cleanup=False):
    # Get all puzzles
    puzzles = redis_connection.zrange("pcupdates", 0, -1)
    current_app.logger.info("transferring puzzles: {0}".format(puzzles))
    for puzzle in puzzles:
        current_app.logger.info("transfer puzzle: {0}".format(puzzle))
        transfer(puzzle, cleanup=cleanup)
        memory = redis_connection.info(section="memory")
        if cleanup:
            current_app.logger.info("used_memory: {used_memory_human}".format(**memory))


def handle_fail(job, exception, exception_func, traceback):
    # TODO: handle fail for janitor; see handle_render_fail of pieceRenderer.py
    current_app.logger.info("Handle janitor fail {0}".format(job.args[0]))


if __name__ == "__main__":
    args = docopt(__doc__)
    config_file = args["--config"]
    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")
    app = make_app(config=config_file, cookie_secret=cookie_secret)

    with app.app_context():
        transferAll(args["--cleanup"])
