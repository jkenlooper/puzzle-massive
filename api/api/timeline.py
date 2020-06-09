from __future__ import absolute_import
from builtins import str
import os
import json
import sqlite3
import time

from flask import current_app, make_response, request, abort, json
from flask.views import MethodView
import requests

from api.app import redis_connection, db
from api.database import rowify, read_query_file, fetch_query_string

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


def add_to_timeline(puzzle_id, player, points=0, timestamp=None, message=""):
    ""

    if timestamp is None:
        _timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    else:
        # TODO: Should verify timestamp is in ISO format.
        _timestamp = timestamp

    if not isinstance(points, int):
        err_msg = {"msg": "points needs to be an integer", "status_code": 400}
        return err_msg

    cur = db.cursor()
    result = cur.execute(
        fetch_query_string("select-internal-puzzle-details-for-puzzle_id.sql"),
        {"puzzle_id": puzzle_id},
    ).fetchall()
    if not result:
        err_msg = {"msg": "No puzzle found", "status_code": 400}
        cur.close()
        return err_msg

    (result, col_names) = rowify(result, cur.description)
    puzzle_data = result[0]
    puzzle = puzzle_data["id"]

    # TODO: The message is not added to the Timeline DB table for now since that
    # information is not currently being used.
    try:
        result = cur.execute(
            fetch_query_string("insert_batchpoints_to_timeline.sql"),
            {
                "puzzle": puzzle,
                "player": player,
                "points": points,
                "timestamp": _timestamp,
            },
        )
    except sqlite3.IntegrityError:
        err_msg = {
            "msg": "Database integrity error. Does the player ({}) exist?".format(
                player
            ),
            "status_code": 400,
        }
        cur.close()
        return err_msg

    cur.close()
    db.commit()
    msg = {"rowcount": result.rowcount, "msg": "Inserted", "status_code": 200}
    return msg


def delete_puzzle_timeline(puzzle_id):
    ""
    cur = db.cursor()
    result = cur.execute(
        fetch_query_string("select-internal-puzzle-details-for-puzzle_id.sql"),
        {"puzzle_id": puzzle_id},
    ).fetchall()
    if not result:
        err_msg = {"msg": "No puzzle found", "status_code": 400}
        cur.close()
        return err_msg

    (result, col_names) = rowify(result, cur.description)
    puzzle_data = result[0]
    puzzle = puzzle_data["id"]

    result = cur.execute(
        fetch_query_string("delete_puzzle_timeline.sql"), {"puzzle": puzzle}
    )
    cur.close()
    db.commit()
    msg = {"rowcount": result.rowcount, "msg": "Deleted", "status_code": 200}
    return msg


class InternalPuzzleTimelineView(MethodView):
    """
    Internal Puzzle Timeline View
    """

    def post(self, puzzle_id):
        "Insert a timeline record for a puzzle."

        data = request.get_json(silent=True)
        if not data:
            err_msg = {"msg": "No JSON data sent", "status_code": 400}
            return make_response(json.jsonify(err_msg), err_msg["status_code"])
        if not {"player", "message", "points", "timestamp"}.issuperset(data.keys()):
            err_msg = {"msg": "Extra fields in JSON data were sent", "status_code": 400}
            return make_response(json.jsonify(err_msg), err_msg["status_code"])
        if not data.get("player"):
            err_msg = {"msg": "Player is required in JSON data", "status_code": 400}
            return make_response(json.jsonify(err_msg), err_msg["status_code"])

        response_msg = add_to_timeline(
            puzzle_id,
            player=data["player"],
            points=data.get("points", 0),
            message=data.get("message", ""),
            timestamp=data.get("timestamp"),
        )
        return make_response(json.jsonify(response_msg), response_msg["status_code"])

    def delete(self, puzzle_id):
        "Delete all timeline records for a puzzle from the database."
        data = request.get_json(silent=True)
        if data:
            err_msg = {
                "msg": "No JSON payload should be sent with DELETE",
                "status_code": 400,
            }
            return make_response(json.jsonify(err_msg), err_msg["status_code"])

        response_msg = delete_puzzle_timeline(puzzle_id)
        return make_response(json.jsonify(response_msg), response_msg["status_code"])
