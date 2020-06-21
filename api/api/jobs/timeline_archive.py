from builtins import str
import os
import sqlite3
import time

from flask import current_app, json
import requests

from api.app import redis_connection, db
from api.database import rowify, fetch_query_string

query_select_timeline_for_puzzle = """
select t.player as p, t.message as m, t.points as c, t.timestamp as t
from Timeline as t
join Puzzle as pz on (pz.id = t.puzzle)
where t.puzzle = :puzzle
"""


def get_next_file(path):
    def numbers(path):
        for filename in os.listdir(path):
            name, ext = os.path.splitext(filename)
            yield int(name)

    try:
        count = max(numbers(path))
    except ValueError:
        # no files found most likely
        count = 0
    count += 1
    return os.path.join(path, "{0}.json".format(count))


def archive_and_clear(puzzle):
    """
    Create an archive file for all timeline data for this puzzle.  Clear the
    timeline entries in the database.
    """
    cur = db.cursor()

    result = cur.execute(
        fetch_query_string("select-all-from-puzzle-by-id.sql"), {"puzzle": puzzle},
    ).fetchall()
    if not result:
        current_app.logger.warn("no puzzle details found for puzzle {}".format(puzzle))
        cur.close()
        return
    (result, col_names) = rowify(result, cur.description)
    puzzle_data = result[0]
    puzzle_id = puzzle_data["puzzle_id"]

    result = cur.execute(
        query_select_timeline_for_puzzle, {"puzzle": puzzle}
    ).fetchall()
    if not result:
        # No timeline?
        cur.close()
        return

    (result, col_names) = rowify(result, cur.description)
    puzzle_directory = os.path.join(
        current_app.config.get("PUZZLE_ARCHIVE"), str(puzzle)
    )
    try:
        os.mkdir(puzzle_directory)
    except OSError:
        # directory already exists
        pass
    timeline_directory = os.path.join(puzzle_directory, "timeline")
    try:
        os.mkdir(timeline_directory)
    except OSError:
        # directory already exists
        pass

    archive_filename = get_next_file(timeline_directory)
    archive_file = open(archive_filename, "w")
    json.dump(result, archive_file, separators=(",", ":"), sort_keys=True)
    archive_file.close()

    r = requests.delete(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/timeline/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle_id,
        ),
    )
    if r.status_code != 200:
        current_app.logger.warning(
            "Puzzle timeline api error. Could not delete timeline entries for puzzle. Skipping {puzzle_id}".format(
                puzzle_id=puzzle_id,
            )
        )
        cur.close()
        return

    redis_connection.delete("timeline:{puzzle}".format(puzzle=puzzle))
    redis_connection.delete("score:{puzzle}".format(puzzle=puzzle))

    cur.close()
