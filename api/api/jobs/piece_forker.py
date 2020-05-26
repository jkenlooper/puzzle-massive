import os
import json
import sys
import subprocess
import time
from shutil import copytree

import sqlite3
from PIL import Image
from flask import current_app

from api.app import db, redis_connection
from api.database import read_query_file, rowify
from api.tools import loadConfig, get_db
from api.jobs.convertPiecesToDB import transfer
from api.constants import (
    MAINTENANCE,
    IN_RENDER_QUEUE,
    REBUILD,
    RENDERING,
    RENDERING_FAILED,
    IN_QUEUE,
    ACTIVE,
    COMPLETED,
    FROZEN,
    PUBLIC,
    PRIVATE,
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
    original_puzzle_id = source_puzzle_data["puzzle_id"]
    source_instance_puzzle_id = source_puzzle_data["instance_puzzle_id"]
    puzzle_id = puzzle_data["puzzle_id"]

    current_app.logger.info(
        "Creating new fork of puzzle {source_instance_puzzle_id} to {puzzle_id}".format(
            source_instance_puzzle_id=source_instance_puzzle_id, puzzle_id=puzzle_id
        )
    )

    if source_puzzle_data["status"] not in (ACTIVE, IN_QUEUE, COMPLETED, FROZEN):
        raise DataError("Source puzzle not in acceptable status")

    result = cur.execute(
        "select * from Puzzle where id = :id", {"id": puzzle_data["id"]},
    ).fetchall()
    if not result:
        raise DataError(
            "Puzzle {puzzle_id} no longer in maintenance status.".format(
                puzzle_id=puzzle_id
            )
        )
    (result, col_names) = rowify(result, cur.description)
    puzzle_data = result[0]
    if puzzle_data["status"] != MAINTENANCE:
        raise DataError(
            "Puzzle {puzzle_id} no longer in maintenance status.".format(
                puzzle_id=puzzle_id
            )
        )
    if puzzle_data["permission"] != PRIVATE:
        raise DataError(
            "Puzzle {puzzle_id} needs to have private (unlisted) permission.".format(
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
    original_puzzle_dir = os.path.join(
        current_app.config["PUZZLE_RESOURCES"], original_puzzle_id
    )
    source_instance_puzzle_dir = os.path.join(
        current_app.config["PUZZLE_RESOURCES"], source_instance_puzzle_id
    )
    puzzle_dir = os.path.join(current_app.config["PUZZLE_RESOURCES"], puzzle_id)
    copytree(source_instance_puzzle_dir, puzzle_dir)
    current_app.logger.debug("copied to {}".format(puzzle_dir))

    # Get all piece props of source puzzle
    transfer(source_puzzle_data["instance_id"], my_db=db)
    query = """select * from Piece where (puzzle = :puzzle)"""
    (piece_properties, col_names) = rowify(
        cur.execute(query, {"puzzle": source_puzzle_data["instance_id"]}).fetchall(),
        cur.description,
    )

    # Commit the piece properties and puzzle resources
    # row and col are really only useful for determining the top left piece when resetting puzzle
    for pc in piece_properties:
        pc["puzzle"] = puzzle_data["id"]
        cur.execute(
            """
            insert or ignore into Piece (id, x, y, r, w, h, b, adjacent, rotate, row, col, status, parent, puzzle) values (
          :id, :x, :y, :r, :w, :h, :b, :adjacent, :rotate, :row, :col, :status, :parent, :puzzle
            );""",
            pc,
        )

    # Check if there is only one piece parent and mark as complete
    is_complete = True
    for index, pc in enumerate(piece_properties):
        if pc["parent"] != piece_properties[max(0, index - 1)]["parent"]:
            is_complete = False
            break

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
    status = ACTIVE
    if is_complete:
        status = COMPLETED
    current_app.logger.debug(
        "set status to {} for {}".format(
            "active" if status == ACTIVE else "completed", puzzle_data["id"]
        )
    )
    cur.execute(
        "update Puzzle set status = :status where id = :id",
        {"status": status, "id": puzzle_data["id"]},
    )
    db.commit()
    cur.close()
