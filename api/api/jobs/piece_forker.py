import os
import sys
import subprocess
import time
from shutil import copytree

import sqlite3
from PIL import Image
from flask import current_app
import requests

from api.app import db, redis_connection
from api.database import fetch_query_string, read_query_file, rowify
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

    puzzle_dir = os.path.join(current_app.config["PUZZLE_RESOURCES"], puzzle_id)

    # Copy the puzzle resources to the new puzzle_dir
    source_instance_puzzle_dir = os.path.join(
        current_app.config["PUZZLE_RESOURCES"], source_instance_puzzle_id
    )
    puzzle_dir = os.path.join(current_app.config["PUZZLE_RESOURCES"], puzzle_id)
    copytree(source_instance_puzzle_dir, puzzle_dir)

    # Get all piece props of source puzzle
    transfer(source_puzzle_data["instance_id"])

    (piece_properties, col_names) = rowify(
        cur.execute(
            """select id, puzzle, adjacent, b, col, h, parent, r, rotate, row, status, w, x, y from Piece where (puzzle = :puzzle)""",
            {"puzzle": source_puzzle_data["instance_id"]},
        ).fetchall(),
        cur.description,
    )

    source_preview_full_attribution = None
    result = cur.execute(
        "select url, attribution from PuzzleFile where puzzle = :source_puzzle and name = :name;",
        {"name": "preview_full", "source_puzzle": source_puzzle_data["id"]},
    ).fetchall()
    if result:
        (result, _) = rowify(result, cur.description)
        source_preview_full_url = result[0]["url"]
        attribution_id = result[0]["attribution"]
    if attribution_id:
        result = cur.execute(
            fetch_query_string("_select_attribution_for_id.sql"),
            {"attribution_id": attribution_id},
        ).fetchall()
        if result:
            (result, _) = rowify(result, cur.description)
            source_preview_full_attribution = {
                "title": result[0]["title"],
                "author_link": result[0]["author_link"],
                "author_name": result[0]["author_name"],
                "source": result[0]["source"],
                "license_name": result[0]["license_name"],
            }

    cur.close()

    # Commit the piece properties and puzzle resources
    # row and col are really only useful for determining the top left piece when resetting puzzle
    for pc in piece_properties:
        pc["puzzle"] = puzzle_data["id"]

    r = requests.post(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/pieces/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle_id,
        ),
        json={"piece_properties": piece_properties},
    )
    if r.status_code != 200:
        raise Exception("Puzzle details api error {}".format(r.json()))

    # Check if there is only one piece parent and mark as complete
    is_complete = True
    for index, pc in enumerate(piece_properties):
        if pc["parent"] != piece_properties[max(0, index - 1)]["parent"]:
            is_complete = False
            break

    # TODO: Copy attribution data on puzzle file if it exists.

    r = requests.post(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle_id,
            file_name="original",
        ),
        json={
            "url": "/resources/{puzzle_id}/original.jpg".format(puzzle_id=puzzle_id),
        },
    )
    if r.status_code != 200:
        raise Exception("Puzzle details api error")

    r = requests.post(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle_id,
            file_name="preview_full",
        ),
        json={
            "url": "/resources/{puzzle_id}/preview_full.jpg".format(puzzle_id=puzzle_id)
            if source_preview_full_url.startswith("/")
            else source_preview_full_url,
            "attribution": source_preview_full_attribution,
        },
    )
    if r.status_code != 200:
        raise Exception("Puzzle details api error {}".format(r.json()))

    r = requests.post(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle_id,
            file_name="pieces",
        ),
        json={
            "url": "/resources/{puzzle_id}/scale-100/raster.png".format(
                puzzle_id=puzzle_id
            ),
        },
    )
    if r.status_code != 200:
        raise Exception("Puzzle details api error")

    r = requests.post(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle_id,
            file_name="pzz",
        ),
        json={
            "url": "/resources/{puzzle_id}/scale-100/raster.css?ts={timestamp}".format(
                puzzle_id=puzzle_id, timestamp=int(time.time())
            )
        },
    )
    if r.status_code != 200:
        raise Exception("Puzzle details api error")

    status = ACTIVE
    if is_complete:
        status = COMPLETED
    r = requests.patch(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle_id,
        ),
        json={"status": status},
    )
    if r.status_code != 200:
        raise Exception("Puzzle details api error")
