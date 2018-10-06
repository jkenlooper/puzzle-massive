import os
import json

from flask import current_app

from app import db
from database import rowify

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
    def numbers( path ):
        for filename in os.listdir(path):
            name, ext = os.path.splitext(filename)
            yield int(name)
    try:
        count = max(numbers(path))
    except ValueError:
        # no files found most likely
        count = 0
    count += 1
    return os.path.join(path, '{0}.json'.format(count))

def archive_and_clear(puzzle):
    """
    Create an archive file for all timeline data for this puzzle.  Clear the
    timeline entries in the database.
    """
    cur = db.cursor()
    result = cur.execute(query_select_timeline_for_puzzle, {'puzzle': puzzle}).fetchall()
    if not result:
        # No timeline?
        return

    (result, col_names) = rowify(result, cur.description)
    archive_directory = current_app.config.get('PUZZLE_ARCHIVE')
    puzzle_directory = os.path.join(archive_directory, str(puzzle))
    try:
        os.mkdir(puzzle_directory)
    except OSError:
        # directory already exists
        pass
    timeline_directory = os.path.join(puzzle_directory, 'timeline')
    try:
        os.mkdir(timeline_directory)
    except OSError:
        # directory already exists
        pass

    archive_filename = get_next_file(timeline_directory)
    archive_file = open(archive_filename, 'w')
    json.dump(result, archive_file, separators=(',',':'), sort_keys=True)
    archive_file.close()

    cur.execute(query_clear_timeline_for_puzzle, {'puzzle': puzzle})

    cur.close()
    db.commit()
