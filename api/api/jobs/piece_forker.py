import os
import json
import sys
import logging
import subprocess
import time
from shutil import copytree

import sqlite3
from PIL import Image
from flask import current_app

from api.app import db, redis_connection
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


class Error(Exception):
    "Base exception for piece_forker"
    pass


class DataError(Error):
    def __init__(self, message):
        self.message = message


def fork_puzzle_pieces(source_puzzle_data, puzzle_data):
    """
    """
    cur = db.cursor()
    source_puzzle_id = source_puzzle_data["puzzle_id"]
    puzzle_id = puzzle_data["puzzle_id"]

    current_app.logger.info(
        "Creating new fork of puzzle {source_puzzle_id} to {puzzle_id}".format(
            source_puzzle_id=source_puzzle_id, puzzle_id=puzzle_id
        )
    )

    result = cur.execute(
        "select status from Puzzle where status = :MAINTENANCE and id = :id",
        {"MAINTENANCE": MAINTENANCE, "id": puzzle_data["id"]},
    ).fetchone()
    if not result:
        raise DataError(
            "Puzzle {puzzle_id} no longer in maintenance status.".format(
                puzzle_id=puzzle_id
            )
        )

    result = cur.execute(
        read_query_file("get_original_puzzle_id_from_puzzle_instance.sql"),
        {"puzzle": puzzle_data["id"]},
    ).fetchone()
    if not result:
        raise DataError(
            "Error with puzzle instance {puzzle_id}.".format(puzzle_id=puzzle_id)
        )

    original_puzzle_id = result[0]
    original_puzzle_dir = os.path.join(
        current_app.config["PUZZLE_RESOURCES"], original_puzzle_id
    )
    puzzle_dir = os.path.join(current_app.config["PUZZLE_RESOURCES"], puzzle_id)

    # Copy the puzzle resources to the new puzzle_dir
    source_puzzle_dir = os.path.join(
        current_app.config["PUZZLE_RESOURCES"], source_puzzle_id
    )
    puzzle_dir = os.path.join(current_app.config["PUZZLE_RESOURCES"], puzzle_id)
    copytree(source_puzzle_dir, puzzle_dir)
    current_app.logger.debug("copied to {}".format(puzzle_dir))

    # TODO: Get all piece props of source puzzle
    piece_properties = []

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
    cur.execute(
        insert_puzzle_file,
        {
            "puzzle": puzzle_data["id"],
            "name": "original",
            "url": "/resources/{puzzle_id}/original.jpg".format(puzzle_id=puzzle_id),
        },
    )
    source_preview_full_url = cur.execute(
        "select url from PuzzleFile where puzzle = :source_puzzle and name = :name;",
        {"name": "preview_full", "source_puzzle": source_puzzle_data["id"]},
    ).fetchone()[0]
    cur.execute(
        insert_puzzle_file,
        {
            "puzzle": puzzle_data["id"],
            "name": "preview_full",
            "url": "/resources/{puzzle_id}/preview_full.jpg".format(puzzle_id=puzzle_id)
            if source_preview_full_url.startswith("/")
            else source_preview_full_url,
        },
    )

    cur.execute(
        insert_puzzle_file,
        {
            "puzzle": puzzle_data["id"],
            "name": "pieces",
            "url": "/resources/{puzzle_id}/scale-100/raster.png".format(
                puzzle_id=puzzle_id
            ),
        },
    )
    cur.execute(
        insert_puzzle_file,
        {
            "puzzle": puzzle_data["id"],
            "name": "pzz",
            "url": "/resources/{puzzle_id}/scale-100/raster.css?ts={timestamp}".format(
                puzzle_id=puzzle_id, timestamp=int(time.time())
            ),
        },
    )
    current_app.logger.debug("set status to active for {}".format(puzzle_data["id"]))
    cur.execute(
        "update Puzzle set status = :status where id = :id",
        {"status": ACTIVE, "id": puzzle_data["id"]},
    )
    db.commit()
    cur.close()
