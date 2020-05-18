import os
import json
import sys
import logging
import subprocess
import time

import sqlite3
from PIL import Image

from api.database import read_query_file
from api.tools import loadConfig, get_db
from api.constants import (
    MAINTENANCE,
    IN_RENDER_QUEUE,
    REBUILD,
    RENDERING,
    RENDERING_FAILED,
    IN_QUEUE,
    ACTIVE,
    PUBLIC,
)

insert_puzzle_file = """
insert into PuzzleFile (puzzle, name, url) values (:puzzle, :name, :url);
"""

# Get the args from the worker and connect to the database
config_file = sys.argv[1]
config = loadConfig(config_file)

db = get_db(config)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if config["DEBUG"] else logging.INFO)


def handle_render_fail(job, exception, exception_func, traceback):
    """
    """
    cur = db.cursor()

    print("Handle render fail")
    for puzzle in job.args:
        print("set puzzle to fail status: {puzzle_id}".format(**puzzle))
        # Update Puzzle data
        cur.execute(
            "update Puzzle set status = :RENDERING_FAILED where status = :RENDERING and id = :id;",
            {
                "RENDERING_FAILED": RENDERING_FAILED,
                "RENDERING": RENDERING,
                "id": puzzle["id"],
            },
        )
    db.commit()
    cur.close()


def fork(*args):
    """
    """
    cur = db.cursor()

    for puzzle in args:
        print("Forking puzzle: {puzzle_id}".format(**puzzle))
        # Set the status of the puzzle to rendering
        # cur.execute(
        #    "update Puzzle set status = :RENDERING where status in (:IN_RENDER_QUEUE, :REBUILD) and id = :id",
        #    {
        #        "RENDERING": RENDERING,
        #        "IN_RENDER_QUEUE": IN_RENDER_QUEUE,
        #        "REBUILD": REBUILD,
        #        "id": puzzle["id"],
        #    },
        # )
        # db.commit()

        result = cur.execute(
            "select status from Puzzle where status = :MAINTENANCE and id = :id",
            {"MAINTENANCE": MAINTENANCE, "id": puzzle["id"]},
        ).fetchone()
        if not result:
            print(
                "Puzzle {puzzle_id} no longer in maintenance status; skipping.".format(
                    **puzzle
                )
            )
            continue

        result = cur.execute(
            read_query_file("get_original_puzzle_id_from_puzzle_instance.sql"),
            {"puzzle": puzzle["id"]},
        ).fetchone()
        if not result:
            print("Error with puzzle instance {puzzle_id} ; skipping.".format(**puzzle))
            continue
        original_puzzle_id = result[0]
        puzzle_id = puzzle["puzzle_id"]
        original_puzzle_dir = os.path.join(
            config["PUZZLE_RESOURCES"], original_puzzle_id
        )
        puzzle_dir = os.path.join(config["PUZZLE_RESOURCES"], puzzle_id)

        copy(puzzle_id)

        piece_properties = []
        for i in range(0, piece_count):

            piece_properties.append(
                {
                    "id": i,
                    "puzzle": puzzle["id"],
                    "x": randint(0, tw),
                    "y": randint(0, th),
                    "w": piece_bboxes[str(i)][2] - piece_bboxes[str(i)][0],
                    "h": piece_bboxes[str(i)][3] - piece_bboxes[str(i)][1],
                    "r": 0,  # mutable rotation of piece
                    "rotate": 0,  # immutable piece orientation
                    "row": -1,  # deprecated
                    "col": -1,  # deprecated
                    "s": 0,  # side
                    "g": None,  # parent
                    "b": 2,  # TODO: will need to be either 0 for dark or 1 for light
                    "status": None,
                }
            )

        # The original.jpg is assumed to be available locally because of migratePuzzleFile.py
        # Clear out any older pieces and their puzzle files, (raster.png,
        # raster.css) but keep preview full.
        # cur.execute(
        #    "delete from Piece where puzzle = :puzzle", {"puzzle": puzzle["id"]}
        # )
        # cur.execute(
        #    "delete from PuzzleFile where puzzle = :puzzle and name in ('pieces', 'pzz')",
        #    {"puzzle": puzzle["id"]},
        # )

        # Commit the piece properties and puzzle resources
        # row and col are really only useful for determining the top left piece when resetting puzzle
        for pc in piece_properties:
            cur.execute(
                """
                insert or ignore into Piece (id, x, y, r, w, h, b, adjacent, rotate, row, col, status, parent, puzzle) values (
              :id, :x, :y, :r, :w, :h, :b, :adjacent, :rotate, :row, :col, :status, :g, :puzzle
                );""",
                pc,
            )

        # Update Puzzle data
        puzzleStatus = ACTIVE

        # TODO: if puzzle is unsplash photo then check if preview_full is still
        # reachable.  If it isn't; then run the set_lost_unsplash_photo from
        # migratePuzzleFile.

        cur.execute(
            "update Puzzle set status = :status where id = :id",
            {"status": puzzleStatus, "id": puzzle["id"]},
        )
        cur.execute(
            insert_puzzle_file,
            {
                "puzzle": puzzle["id"],
                "name": "pieces",
                "url": "/resources/{puzzle_id}/scale-100/raster.png".format(**puzzle),
            },
        )
        cur.execute(
            insert_puzzle_file,
            {
                "puzzle": puzzle["id"],
                "name": "pzz",
                "url": "/resources/{puzzle_id}/scale-100/raster.css?ts={timestamp}".format(
                    puzzle_id=puzzle["puzzle_id"], timestamp=int(time.time())
                ),
            },
        )
        db.commit()
        cur.close()

        whitelist = [
            "original.jpg",
            "preview_full.jpg",
            "resized-original.jpg",
            "scale-100",
            "raster.css",
            "raster.png",
        ]
        cleanup(puzzle["puzzle_id"], whitelist)


def cleanup(puzzle_id, whitelist):
    puzzle_dir = os.path.join(config["PUZZLE_RESOURCES"], puzzle_id)
    for (dirpath, dirnames, filenames) in os.walk(puzzle_dir, False):
        for filename in filenames:
            if filename not in whitelist:
                os.unlink(os.path.join(dirpath, filename))
        for dirname in dirnames:
            if dirname not in whitelist:
                os.rmdir(os.path.join(dirpath, dirname))
