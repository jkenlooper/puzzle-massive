import os
import re

from flask import current_app
import requests

from api.app import db
from api.database import fetch_query_string, rowify
from api.jobs.convertPiecesToDB import transfer
from api.puzzle_resource import PuzzleResource
from api.constants import (
    MAINTENANCE,
    IN_QUEUE,
    ACTIVE,
    COMPLETED,
    FROZEN,
    PRIVATE,
)


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

    # Copy the puzzle resources to the new target puzzle resource location
    raster_css_filename = ""
    raster_png_filename = ""
    pr_target = PuzzleResource(puzzle_id, current_app.config, is_local_resource=current_app.config["LOCAL_PUZZLE_RESOURCES"])
    pr_source = PuzzleResource(source_instance_puzzle_id, current_app.config, is_local_resource=not source_puzzle_data["url"].startswith("http") or not source_puzzle_data["url"].startswith("//"))
    listing = pr_source.list()
    for path in listing:
        filename = os.path.basename(path)
        if re.match(r"(original|preview_full|resized-original)\.([^.]+\.)?jpg", filename) is not None:
            # When forking a puzzle, the original and preview_full images will
            # remain with the original puzzle that this instance is being made
            # from.
            continue
        if re.match(r"raster\.([^.]+\.)?css", filename) is not None:
            raster_css_filename = filename
        if re.match(r"raster\.([^.]+\.)?png", filename) is not None:
            raster_png_filename = filename
        pr_target.copy_file(pr_source, path)

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

    CDN_BASE_URL = current_app.config["CDN_BASE_URL"]
    prefix_resources_url = "" if current_app.config["LOCAL_PUZZLE_RESOURCES"] else CDN_BASE_URL
    r = requests.post(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle_id,
            file_name="pieces",
        ),
        json={
            "url": f"{prefix_resources_url}/resources/{puzzle_id}/scale-100/{raster_png_filename}"
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
            "url": f"{prefix_resources_url}/resources/{puzzle_id}/scale-100/{raster_css_filename}"
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
