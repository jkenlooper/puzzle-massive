from __future__ import absolute_import
from builtins import str
import os
import json

from .database import rowify, read_query_file

query_select_timeline_for_puzzle = """
select t.player as p, t.message as m, t.points as c, t.timestamp as t
from Timeline as t
join Puzzle as pz on (pz.id = t.puzzle)
where t.puzzle = :puzzle
"""

query_clear_timeline_for_puzzle = """
delete from Timeline where puzzle = :puzzle
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


def archive_and_clear(puzzle, db, redis_connection, archive_directory):
    """
    Create an archive file for all timeline data for this puzzle.  Clear the
    timeline entries in the database.
    """
    cur = db.cursor()
    result = cur.execute(
        query_select_timeline_for_puzzle, {"puzzle": puzzle}
    ).fetchall()
    if not result:
        # No timeline?
        return

    (result, col_names) = rowify(result, cur.description)
    puzzle_directory = os.path.join(archive_directory, str(puzzle))
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

    cur.execute(read_query_file("delete_puzzle_timeline.sql"), {"puzzle": puzzle})
    redis_connection.delete("timeline:{puzzle}".format(puzzle=puzzle))
    redis_connection.delete("score:{puzzle}".format(puzzle=puzzle))

    cur.close()
    db.commit()
