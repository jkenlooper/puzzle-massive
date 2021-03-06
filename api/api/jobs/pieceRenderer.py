"""pieceRenderer.py - Create puzzle pieces for puzzles in render queue

Usage: pieceRenderer.py [--config <file>]
       pieceRenderer.py --help
       pieceRenderer.py --list

Options:
    -h --help           Show this screen.
    --config <file>     Set config file. [default: site.cfg]
    --list              List puzzles that are being rendered or are in render queue
"""

from __future__ import print_function
from __future__ import division
from builtins import map
from builtins import str
from builtins import range
from past.utils import old_div
import os
import json
import sys
import logging
from random import randint
import subprocess
import time
from docopt import docopt

import sqlite3
from PIL import Image
from piecemaker.base import JigsawPieceClipsSVG, Pieces
from piecemaker.adjacent import Adjacent
from flask import current_app
import requests

from api.app import redis_connection, db, make_app
from api.database import read_query_file, rowify
from api.tools import loadConfig, get_db
from api.constants import (
    IN_RENDER_QUEUE,
    REBUILD,
    RENDERING,
    RENDERING_FAILED,
    IN_QUEUE,
    ACTIVE,
    PUBLIC,
)


# https://www.imagemagick.org/script/architecture.php#cache
# Need to update the limits in /etc/ImageMagick-6/policy.xml to something like:
#
#  <policy domain="resource" name="memory" value="2GiB"/>
#  <policy domain="resource" name="map" value="1GiB"/>
#  <policy domain="resource" name="width" value="64KP"/>
#  <policy domain="resource" name="height" value="64KP"/>
#  <policy domain="resource" name="area" value="512MB"/>

#  <policy domain="resource" name="disk" value="1GiB"/>

MIN_PIECE_SIZE = 64
MAX_PIECE_SIZE = 64
MAX_PIECES = 10000
MAX_PIXELS = (MIN_PIECE_SIZE * MIN_PIECE_SIZE) * MAX_PIECES

insert_puzzle_file = """
insert into PuzzleFile (puzzle, name, url) values (:puzzle, :name, :url);
"""


def handle_render_fail(job, exception, exception_func, traceback):
    """
    """
    print("Handle render fail")
    for puzzle in job.args:
        set_render_fail_on_puzzle(puzzle)


def set_render_fail_on_puzzle(puzzle):
    print("set puzzle to fail status: {puzzle_id}".format(**puzzle))
    # Set the status of the puzzle to rendering failed
    r = requests.patch(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle["puzzle_id"],
        ),
        json={"status": RENDERING_FAILED},
    )
    if r.status_code != 200:
        raise Exception("Puzzle details api error")


def render_all():
    ""
    cur = db.cursor()

    result = cur.execute(
        "select * from Puzzle where status in (:IN_RENDER_QUEUE, :REBUILD)",
        {"IN_RENDER_QUEUE": IN_RENDER_QUEUE, "REBUILD": REBUILD,},
    ).fetchall()
    if not result:
        print("no puzzles found in render or rebuild queues")
        return
    (result, col_names) = rowify(result, cur.description)
    job = {"args": result}
    for puzzle in result:
        try:
            render([puzzle])
        except:
            set_render_fail_on_puzzle(puzzle)


def list_all():
    ""
    cur = db.cursor()

    result = cur.execute(
        "select * from Puzzle where status in (:IN_RENDER_QUEUE, :REBUILD, :RENDERING, :RENDERING_FAILED) order by status",
        {
            "IN_RENDER_QUEUE": IN_RENDER_QUEUE,
            "REBUILD": REBUILD,
            "RENDERING": RENDERING,
            "RENDERING_FAILED": RENDERING_FAILED,
        },
    ).fetchall()
    if not result:
        print(
            "no puzzles found in render or rebuild queues. No puzzles rendering or have failed rendering."
        )
        return
    (result, col_names) = rowify(result, cur.description)
    puzzles_grouped_by_status = {
        IN_RENDER_QUEUE: [],
        REBUILD: [],
        RENDERING: [],
        RENDERING_FAILED: [],
    }
    for puzzle in result:
        puzzles_grouped_by_status[puzzle["status"]].append(puzzle)

    for status, words in [
        (IN_RENDER_QUEUE, "in render queue"),
        (REBUILD, "in rebuild queue"),
        (RENDERING, "rendering"),
        (RENDERING_FAILED, "that failed rendering"),
    ]:
        if len(puzzles_grouped_by_status[status]):
            print(
                "\n{count} puzzles {words}:".format(
                    count=len(puzzles_grouped_by_status[status]), words=words
                )
            )
            for puzzle in puzzles_grouped_by_status[status]:
                print("{pieces} pieces, ({id}) {puzzle_id}".format(**puzzle))


def render(*args):
    """
    Render any puzzles that are in the render queue.
    Each puzzle should exist in the Puzzle db with the IN_RENDER_QUEUE or REBUILD status
    and have an original.jpg file.
    """
    # Delete old piece properties if existing
    # Delete old PuzzleFile for name if existing
    # TODO: update preview image in PuzzleFile?
    cur = db.cursor()

    for puzzle in args:
        current_app.logger.info("Rendering puzzle: {puzzle_id}".format(**puzzle))

        result = cur.execute(
            read_query_file("select-internal-puzzle-details-for-puzzle_id.sql"),
            {"puzzle_id": puzzle["puzzle_id"]},
        ).fetchall()
        if not result:
            current_app.logger.info(
                "Puzzle {puzzle_id} not available; skipping.".format(**puzzle)
            )
            continue

        puzzle_data = rowify(result, cur.description,)[0][0]
        if puzzle_data["status"] not in (IN_RENDER_QUEUE, REBUILD):
            current_app.logger.info(
                "Puzzle {puzzle_id} no longer in rendering status; skipping.".format(
                    **puzzle
                )
            )
            continue

        # Set the status of the puzzle to rendering
        r = requests.patch(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                HOSTAPI=current_app.config["HOSTAPI"],
                PORTAPI=current_app.config["PORTAPI"],
                puzzle_id=puzzle["puzzle_id"],
            ),
            json={"status": RENDERING},
        )
        if r.status_code != 200:
            raise Exception("Puzzle details api error")

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
            current_app.config["PUZZLE_RESOURCES"], original_puzzle_id
        )
        puzzle_dir = os.path.join(current_app.config["PUZZLE_RESOURCES"], puzzle_id)

        # If it is being rebuilt then delete all the other resources.
        cleanup(puzzle_id, ["original.jpg", "preview_full.jpg"])

        scaled_sizes = [
            100,
        ]

        # Create the preview full if it is a new original puzzle. A puzzle is
        # considered to be 'new' if status was IN_RENDER_QUEUE and not REBUILD.
        # TODO: use requests.get to get original.jpg and run in another thread
        if original_puzzle_id == puzzle_id and puzzle["status"] == IN_RENDER_QUEUE:
            im = Image.open(os.path.join(original_puzzle_dir, "original.jpg")).copy()
            im.thumbnail(size=(384, 384))
            im.save(os.path.join(puzzle_dir, "preview_full.jpg"))
            im.close()

        # TODO: get path of original.jpg via the PuzzleFile query
        # TODO: use requests.get to get original.jpg and run in another thread
        imagefile = os.path.join(original_puzzle_dir, "original.jpg")

        im = Image.open(imagefile)
        (width, height) = im.size
        im.close()

        # Scale down puzzle image to avoid have pieces too big
        # min_pixels = (MIN_PIECE_SIZE * MIN_PIECE_SIZE) * int(puzzle['pieces'])
        max_pixels = min(
            MAX_PIXELS, (MAX_PIECE_SIZE * MAX_PIECE_SIZE) * int(puzzle["pieces"])
        )
        im_pixels = width * height
        if im_pixels > max_pixels:
            resizedimagefile = os.path.join(puzzle_dir, "resized-original.jpg")
            # The image is too big which would create piece sizes larger then the MAX_PIECE_SIZE
            # resize the image using image magick @
            subprocess.call(
                [
                    "convert",
                    imagefile,
                    "-resize",
                    "{0}@".format(max_pixels),
                    "-strip",
                    "-quality",
                    "85%",
                    resizedimagefile,
                ]
            )
            im = Image.open(resizedimagefile)
            (width, height) = im.size
            im_pixels = width * height
            imagefile = resizedimagefile
            im.close()

        # Create svg lines
        jpc = JigsawPieceClipsSVG(
            width=width,
            height=height,
            pieces=int(puzzle["pieces"]),
            minimum_piece_size=MIN_PIECE_SIZE,
        )
        svgfile = os.path.join(puzzle_dir, "lines.svg")
        f = open(svgfile, "w")
        f.write(jpc.svg())
        f.close()

        # Create pieces
        piece_count = 0
        dimensions = {}
        for scale in scaled_sizes:
            scale = int(scale)
            scaled_dir = os.path.join(puzzle_dir, "scale-%i" % scale)
            os.mkdir(scaled_dir)

            # max_pixels is 0 to prevent resizing, since this is handled before creating piece clips svg
            # Skip creating the svg files for each piece by setting vector to False (too memory intensive)
            pieces = Pieces(
                svgfile, imagefile, scaled_dir, scale=scale, max_pixels=0, vector=False
            )

            pieces.cut()

            pieces.generate_resources()

            piece_count = len(pieces.pieces)
            piece_bboxes = pieces.pieces
            dimensions[scale] = {
                "width": pieces.width,
                "height": pieces.height,
                "table_width": int(pieces.width * 2.5),
                "table_height": int(pieces.height * 2.5),
                "board_url": "puzzle_board-%s.html" % scale,
            }

        tw = dimensions[100]["table_width"]
        th = dimensions[100]["table_height"]

        # Update the table width and height, set the new piece count
        r = requests.patch(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                HOSTAPI=current_app.config["HOSTAPI"],
                PORTAPI=current_app.config["PORTAPI"],
                puzzle_id=puzzle["puzzle_id"],
            ),
            json={"pieces": piece_count, "table_width": tw, "table_height": th,},
        )
        if r.status_code != 200:
            raise Exception("Puzzle details api error")

        # Update the css file with dimensions for puzzle outline
        cssfile = open(os.path.join(puzzle_dir, "scale-100", "raster.css"), "a")
        cssfile.write(
            "[id=puzzle-outline]{{width:{width}px;height:{height}px;left:{left}px;top:{top}px;}}".format(
                width=pieces.width,
                height=pieces.height,
                left=int(round(old_div((tw - pieces.width), 2))),
                top=int(round(old_div((th - pieces.height), 2))),
            )
        )
        cssfile.close()

        # Get the top left piece by checking the bounding boxes
        top_left_piece = "0"
        minLeft = piece_bboxes[top_left_piece][0]
        minTop = piece_bboxes[top_left_piece][1]
        for key in list(piece_bboxes.keys()):
            if piece_bboxes[key][0] <= minLeft and piece_bboxes[key][1] <= minTop:
                top_left_piece = key
                minLeft = piece_bboxes[key][0]
                minTop = piece_bboxes[key][1]
        top_left_piece = int(top_left_piece)

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
                    # "s": 0,  # side
                    "parent": None,  # parent
                    "b": 2,  # TODO: will need to be either 0 for dark or 1 for light
                    "status": None,
                }
            )

        # Set the top left piece to the top left corner and make it immovable
        piece_properties[top_left_piece]["x"] = int(
            round(old_div((tw - pieces.width), 2))
        )
        piece_properties[top_left_piece]["y"] = int(
            round(old_div((th - pieces.height), 2))
        )
        piece_properties[top_left_piece]["status"] = 1
        piece_properties[top_left_piece]["parent"] = top_left_piece
        # set row and col for finding the top left piece again after reset of puzzle
        piece_properties[top_left_piece]["row"] = 0
        piece_properties[top_left_piece]["col"] = 0

        # create index.json
        data = {
            "version": "alpha",
            "generator": "piecemaker",
            "scaled": scaled_sizes,
            "sides": [0],
            "piece_count": piece_count,
            "image_author": "none",
            "image_link": "none",
            "image_title": "none",
            "image_description": "none",
            "puzzle_author": "yup",
            "puzzle_link": "yup",
            "scaled_dimensions": dimensions,
            "piece_properties": piece_properties,
        }
        f = open(os.path.join(puzzle_dir, "index.json"), "w")
        json.dump(data, f)
        f.close()

        # Create adjacent pieces
        adjacent_pieces = None
        if (
            False
        ):  # TODO: Use the overlapping masks approach when using a custom cut lines
            first_scaled_dir = os.path.join(puzzle_dir, "scale-%i" % scaled_sizes[0])
            adjacent = Adjacent(first_scaled_dir, by_overlap=True)
            adjacent_pieces = adjacent.adjacent_pieces
        else:  # Find adjacent pieces by bounding boxes only and skip corners
            first_scaled_dir = os.path.join(puzzle_dir, "scale-%i" % scaled_sizes[0])
            adjacent = Adjacent(first_scaled_dir, by_overlap=False)
            adjacent_pieces = adjacent.adjacent_pieces
            filtered_adjacent_pieces = {}

            # filter out the corner adjacent pieces
            for target_id, target_adjacent_list in list(adjacent_pieces.items()):
                target_bbox = piece_bboxes[target_id]  # [0, 0, 499, 500]
                target_center_x = target_bbox[0] + int(
                    round(old_div((target_bbox[2] - target_bbox[0]), 2))
                )
                target_center_y = target_bbox[1] + int(
                    round(old_div((target_bbox[3] - target_bbox[1]), 2))
                )
                filtered_adjacent_list = []
                for adjacent_id in target_adjacent_list:
                    adjacent_bbox = piece_bboxes[adjacent_id]  # [0, 347, 645, 996]
                    left = (adjacent_bbox[0] < target_center_x) and (
                        adjacent_bbox[2] < target_center_x
                    )
                    top = (adjacent_bbox[1] < target_center_y) and (
                        adjacent_bbox[3] < target_center_y
                    )
                    right = (adjacent_bbox[0] > target_center_x) and (
                        adjacent_bbox[2] > target_center_x
                    )
                    bottom = (adjacent_bbox[1] > target_center_y) and (
                        adjacent_bbox[3] > target_center_y
                    )

                    if (
                        (top and left)
                        or (top and right)
                        or (bottom and left)
                        or (bottom and right)
                    ):
                        loc = []
                        if top and left:
                            loc.append("top left")
                        if top and right:
                            loc.append("top right")
                        if bottom and left:
                            loc.append("bottom left")
                        if bottom and right:
                            loc.append("bottom right")
                        # print("adjacent piece: {0} is {2} corner piece of {1}".format(adjacent_id, target_id, loc))
                        # print("adjacent bbox: {0}".format(adjacent_bbox))
                        # print("target bbox: {0}".format(target_bbox))
                    else:
                        filtered_adjacent_list.append(adjacent_id)

                filtered_adjacent_pieces[target_id] = filtered_adjacent_list
            adjacent_pieces = filtered_adjacent_pieces
            # print(filtered_adjacent_pieces)
            # for f, g in filtered_adjacent_pieces.items():
            #    print("{0} with {1} adjacent pieces: {2}".format(f, len(g), g))

        f = open(os.path.join(puzzle_dir, "adjacent.json"), "w")
        json.dump(adjacent_pieces, f)
        f.close()

        # Create adjacent offsets for the scale
        for pc in piece_properties:
            origin_x = piece_bboxes[str(pc["id"])][0]
            origin_y = piece_bboxes[str(pc["id"])][1]
            offsets = {}
            for adj_pc in adjacent_pieces[str(pc["id"])]:
                x = piece_bboxes[adj_pc][0] - origin_x
                y = piece_bboxes[adj_pc][1] - origin_y
                offsets[adj_pc] = "{x},{y}".format(x=x, y=y)
            adjacent_str = " ".join(
                map(
                    lambda k, v: "{0}:{1}".format(k, v),
                    list(offsets.keys()),
                    list(offsets.values()),
                )
            )
            pc["adjacent"] = adjacent_str

        # The original.jpg is assumed to be available locally because of migratePuzzleFile.py
        # Clear out any older pieces and their puzzle files, (raster.png,
        # raster.css) but keep preview full.
        r = requests.delete(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/pieces/".format(
                HOSTAPI=current_app.config["HOSTAPI"],
                PORTAPI=current_app.config["PORTAPI"],
                puzzle_id=puzzle["puzzle_id"],
            )
        )
        if r.status_code != 200:
            raise Exception(
                "Puzzle pieces api error when deleting pieces for puzzle {}".format(
                    puzzle["puzzle_id"]
                )
            )

        for name in [
            "pieces",
            "pzz",
        ]:
            r = requests.delete(
                "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                    HOSTAPI=current_app.config["HOSTAPI"],
                    PORTAPI=current_app.config["PORTAPI"],
                    puzzle_id=puzzle["puzzle_id"],
                    file_name=name,
                ),
            )
            if r.status_code != 200:
                raise Exception(
                    "Puzzle file api error when deleting file '{}' for puzzle {}".format(
                        name, puzzle["puzzle_id"]
                    )
                )

        # Commit the piece properties and puzzle resources
        # row and col are really only useful for determining the top left piece when resetting puzzle
        r = requests.post(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/pieces/".format(
                HOSTAPI=current_app.config["HOSTAPI"],
                PORTAPI=current_app.config["PORTAPI"],
                puzzle_id=puzzle["puzzle_id"],
            ),
            json={"piece_properties": piece_properties},
        )
        if r.status_code != 200:
            raise Exception(
                "Puzzle pieces api error. Failed to post pieces. {}".format(r)
            )

        # Update Puzzle data
        puzzleStatus = ACTIVE
        if original_puzzle_id == puzzle_id and puzzle["permission"] == PUBLIC:
            puzzleStatus = IN_QUEUE

        # TODO: if puzzle is unsplash photo then check if preview_full is still
        # reachable.  If it isn't; then run the set_lost_unsplash_photo from
        # migratePuzzleFile.

        r = requests.patch(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                HOSTAPI=current_app.config["HOSTAPI"],
                PORTAPI=current_app.config["PORTAPI"],
                puzzle_id=puzzle["puzzle_id"],
            ),
            json={
                "status": puzzleStatus,
                "m_date": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            },
        )
        if r.status_code != 200:
            raise Exception(
                "Puzzle details api error when updating status and m_date on newly rendered puzzle"
            )

        for (name, url) in [
            (
                "pieces",
                "/resources/{puzzle_id}/scale-100/raster.png".format(
                    puzzle_id=puzzle["puzzle_id"]
                ),
            ),
            (
                "pzz",
                "/resources/{puzzle_id}/scale-100/raster.css?ts={timestamp}".format(
                    puzzle_id=puzzle["puzzle_id"], timestamp=int(time.time())
                ),
            ),
        ]:
            r = requests.post(
                "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                    HOSTAPI=current_app.config["HOSTAPI"],
                    PORTAPI=current_app.config["PORTAPI"],
                    puzzle_id=puzzle["puzzle_id"],
                    file_name=name,
                ),
                json={"url": url,},
            )
            if r.status_code != 200:
                raise Exception(
                    "Puzzle file api error when adding file '{}' on newly rendered puzzle".format(
                        name
                    )
                )

        cur.close()

        keep_list = [
            "original.jpg",
            "preview_full.jpg",
            "resized-original.jpg",
            "scale-100",
            "raster.css",
            "raster.png",
        ]
        cleanup(puzzle["puzzle_id"], keep_list)


def cleanup(puzzle_id, keep_list):
    puzzle_dir = os.path.join(current_app.config["PUZZLE_RESOURCES"], puzzle_id)
    for (dirpath, dirnames, filenames) in os.walk(puzzle_dir, False):
        for filename in filenames:
            if filename not in keep_list:
                os.unlink(os.path.join(dirpath, filename))
        for dirname in dirnames:
            if dirname not in keep_list:
                os.rmdir(os.path.join(dirpath, dirname))


def main():
    args = docopt(__doc__)
    config_file = args["--config"]
    show_list = args.get("--list")
    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")
    app = make_app(config=config_file, cookie_secret=cookie_secret)

    with app.app_context():
        if not show_list:
            render_all()
        else:
            list_all()


if __name__ == "__main__":
    main()
