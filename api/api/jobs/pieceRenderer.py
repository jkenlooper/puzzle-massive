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
from builtins import str
import os
import json
import subprocess
import time
from docopt import docopt
from shutil import rmtree, move
import tempfile
import uuid

from flask import current_app
import requests

from api.app import db, make_app
from api.database import read_query_file, rowify
from api.tools import loadConfig
from api.puzzle_resource import PuzzleResource
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

MIN_PIECE_SIZE = 35
MAX_PIECE_SIZE = 71


def handle_render_fail(job, exception, exception_func, traceback):
    """"""
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
        {
            "IN_RENDER_QUEUE": IN_RENDER_QUEUE,
            "REBUILD": REBUILD,
        },
    ).fetchall()
    if not result:
        print("no puzzles found in render or rebuild queues")
        return
    (result, col_names) = rowify(result, cur.description)
    cur.close()
    for puzzle in result:
        try:
            render([puzzle])
        except Exception:
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
        cur.close()
        return
    (result, col_names) = rowify(result, cur.description)
    cur.close()
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


def render(puzzles):
    """
    Render any puzzles that are in the render queue.
    Each puzzle should exist in the Puzzle db with the IN_RENDER_QUEUE or REBUILD status
    and have an original.jpg file.
    """
    # Delete old piece properties if existing
    # Delete old PuzzleFile for name if existing
    # TODO: update preview image in PuzzleFile?

    for puzzle in puzzles:
        cur = db.cursor()
        current_app.logger.info("Rendering puzzle: {puzzle_id}".format(**puzzle))

        result = cur.execute(
            read_query_file("select-internal-puzzle-details-for-puzzle_id.sql"),
            {"puzzle_id": puzzle["puzzle_id"]},
        ).fetchall()
        if not result:
            current_app.logger.info(
                "Puzzle {puzzle_id} not available; skipping.".format(**puzzle)
            )
            cur.close()
            continue

        puzzle_data = rowify(result, cur.description,)[
            0
        ][0]
        cur.close()
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

        cur = db.cursor()
        result = cur.execute(
            read_query_file("get_original_puzzle_id_from_puzzle_instance.sql"),
            {"puzzle": puzzle["id"], "puzzle_file_name": "original"},
        ).fetchone()
        cur.close()
        if not result:
            print("Error with puzzle instance {puzzle_id} ; skipping.".format(**puzzle))
            continue
        original_puzzle_id = result[0]
        original_original_image = result[1]
        original_image_basename = os.path.basename(original_original_image)

        pr_original = PuzzleResource(original_puzzle_id, current_app.config, is_local_resource=not original_original_image.startswith("http") and not original_original_image.startswith("//"))
        imagefile = pr_original.yank_file(original_image_basename)

        puzzle_id = puzzle["puzzle_id"]
        tmp_dir = tempfile.mkdtemp()
        tmp_puzzle_dir = os.path.join(tmp_dir, puzzle_id)
        os.mkdir(tmp_puzzle_dir)

        preview_full_basename = os.path.basename(puzzle["preview_full"])

        subprocess.run(
            [
                "./bin/piecemaker",
                "--dir",
                tmp_puzzle_dir,
                "--scaled-sizes=100",
                "--minimum-piece-size",
                str(MIN_PIECE_SIZE),
                "--maximum-piece-size",
                str(MAX_PIECE_SIZE),
                "--number-of-pieces",
                str(puzzle["pieces"]),
                "--variant=interlockingnubs",
                imagefile,
            ],
            check=True,
        )
        with open(os.path.join(tmp_puzzle_dir, "index.json"), "r") as piecemaker_index_json:
            piecemaker_index = json.load(piecemaker_index_json)
        full_size = piecemaker_index["full_size"]

        # Rename files to match the older names for now.

        slip = uuid.uuid4().hex[:10]
        move(
            os.path.join(tmp_puzzle_dir, f"size-{full_size}"),
            os.path.join(tmp_puzzle_dir, "scale-100"),
        )
        with open(
            os.path.join(tmp_puzzle_dir, "scale-100", "sprite_raster.css"), "r"
        ) as css:
            sprite_raster = css.read()
        with open(os.path.join(tmp_puzzle_dir, "scale-100", "sprite_p.css"), "r") as css:
            sprite_p = css.read()
        with open(os.path.join(tmp_puzzle_dir, "scale-100", f"raster.{slip}.css"), "w") as css:
            css.write(sprite_p.replace("sprite_without_padding.png", f"raster.{slip}.png"))
            css.write(sprite_raster)
        move(
            os.path.join(tmp_puzzle_dir, "scale-100", "sprite_without_padding.png"),
            os.path.join(tmp_puzzle_dir, "scale-100", f"raster.{slip}.png"),
        )

        with open(
            os.path.join(tmp_puzzle_dir, "scale-100", "pieces.json"), "r"
        ) as pieces_json:
            piece_bboxes = json.load(pieces_json)

        # Update the table width and height, set the new piece count
        r = requests.patch(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                HOSTAPI=current_app.config["HOSTAPI"],
                PORTAPI=current_app.config["PORTAPI"],
                puzzle_id=puzzle_id,
            ),
            json={
                "pieces": piecemaker_index["piece_count"],
                "table_width": piecemaker_index["table_width"],
                "table_height": piecemaker_index["table_height"],
            },
        )
        if r.status_code != 200:
            raise Exception("Puzzle details api error")

        # Update the css file with dimensions for puzzle outline
        puzzle_outline_css = "".join(
            [
                "[id=puzzle-outline]{{",
                "width:{width}px;",
                "height:{height}px;",
                "left:{left}px;",
                "top:{top}px;",
                "}}",
            ]
        )
        cssfile = os.path.join(tmp_puzzle_dir, "scale-100", f"raster.{slip}.css")
        with open(cssfile, "a") as f:
            f.write(
                puzzle_outline_css.format(
                    width=piecemaker_index["image_width"],
                    height=piecemaker_index["image_height"],
                    left=piecemaker_index["outline_bbox"][0],
                    top=piecemaker_index["outline_bbox"][1],
                )
            )

        # Get the top left piece by checking the bounding boxes
        top_left_piece = "0"
        min_left = piece_bboxes[top_left_piece][0]
        min_top = piece_bboxes[top_left_piece][1]
        for i, bbox in piece_bboxes.items():
            if bbox[0] <= min_left and bbox[1] <= min_top:
                top_left_piece = i
                min_left = bbox[0]
                min_top = bbox[1]
        top_left_piece = int(top_left_piece)

        piece_properties = []
        for piecemaker_piece_property in piecemaker_index["piece_properties"]:
            piecemaker_piece_property.update(
                {
                    "id": int(piecemaker_piece_property["id"]),
                    "puzzle": puzzle["id"],
                    "row": -1,  # deprecated
                    "col": -1,  # deprecated
                    # "s": 0,  # side
                    "parent": None,  # parent
                    "b": 2,  # TODO: will need to be either 0 for dark or 1 for light
                    "status": None,
                }
            )
            # The group and side (g, s) from piecemaker are not relevant to how
            # Puzzle Massive uses these same keys. The outline x and y (ox, oy)
            # are not used here yet.
            for auxprop in ("g", "s", "ox", "oy"):
                del piecemaker_piece_property[auxprop]
            piece_properties.append(piecemaker_piece_property)

        # Set the top left piece to the top left corner and make it immovable
        piece_properties[top_left_piece]["x"] = int(
            round(
                (piecemaker_index["table_width"] - piecemaker_index["image_width"])
                * 0.5
            )
        )
        piece_properties[top_left_piece]["y"] = int(
            round(
                (piecemaker_index["table_height"] - piecemaker_index["image_height"])
                * 0.5
            )
        )
        piece_properties[top_left_piece]["status"] = 1
        piece_properties[top_left_piece]["parent"] = top_left_piece
        # set row and col for finding the top left piece again after reset of puzzle
        piece_properties[top_left_piece]["row"] = 0
        piece_properties[top_left_piece]["col"] = 0

        with open(os.path.join(tmp_puzzle_dir, "adjacent.json"), "r") as f:
            adjacent_pieces = json.load(f)

        # Save the new files and replace any older ones.
        keep_list = [
            original_image_basename,
            preview_full_basename,
            "scale-100",
            f"raster.{slip}.css",
            f"raster.{slip}.png",
        ]
        cleanup_dir(tmp_puzzle_dir, keep_list)
        pr = PuzzleResource(puzzle_id, current_app.config, is_local_resource=current_app.config["LOCAL_PUZZLE_RESOURCES"])
        pr.put(tmp_puzzle_dir)

        # Create adjacent offsets for the scale
        for pc in piece_properties:
            origin_x = piece_bboxes[str(pc["id"])][0]
            origin_y = piece_bboxes[str(pc["id"])][1]
            offsets = []
            for adj_pc in adjacent_pieces[str(pc["id"])]:
                x = piece_bboxes[adj_pc][0] - origin_x
                y = piece_bboxes[adj_pc][1] - origin_y
                offsets.append(f"{adj_pc}:{x},{y}")
            # adjacent_str = " ".join(
            #    map(
            #        lambda k, v: "{0}:{1}".format(k, v),
            #        list(offsets.keys()),
            #        list(offsets.values()),
            #    )
            # )
            pc["adjacent"] = " ".join(offsets)

        # The original.jpg is assumed to be available locally because of migratePuzzleFile.py
        # Clear out any older pieces and their puzzle files, (raster.png,
        # raster.css) but keep preview full.
        r = requests.delete(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/pieces/".format(
                HOSTAPI=current_app.config["HOSTAPI"],
                PORTAPI=current_app.config["PORTAPI"],
                puzzle_id=puzzle_id,
            )
        )
        if r.status_code != 200:
            raise Exception(
                "Puzzle pieces api error when deleting pieces for puzzle {}".format(
                    puzzle_id
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
                    puzzle_id=puzzle_id,
                    file_name=name,
                ),
            )
            if r.status_code != 200:
                raise Exception(
                    "Puzzle file api error when deleting file '{}' for puzzle {}".format(
                        name, puzzle_id
                    )
                )

        # Commit the piece properties and puzzle resources
        # row and col are really only useful for determining the top left piece when resetting puzzle
        r = requests.post(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/pieces/".format(
                HOSTAPI=current_app.config["HOSTAPI"],
                PORTAPI=current_app.config["PORTAPI"],
                puzzle_id=puzzle_id,
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
                puzzle_id=puzzle_id,
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

        CDN_BASE_URL = current_app.config["CDN_BASE_URL"]
        prefix_resources_url = "" if current_app.config["LOCAL_PUZZLE_RESOURCES"] else CDN_BASE_URL
        for (name, url) in [
            (
                "pieces",
                f"{prefix_resources_url}/resources/{puzzle_id}/scale-100/raster.{slip}.png",
            ),
            (
                "pzz",
                f"{prefix_resources_url}/resources/{puzzle_id}/scale-100/raster.{slip}.css"
            ),
        ]:
            r = requests.post(
                "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                    HOSTAPI=current_app.config["HOSTAPI"],
                    PORTAPI=current_app.config["PORTAPI"],
                    puzzle_id=puzzle_id,
                    file_name=name,
                ),
                json={
                    "url": url,
                },
            )
            if r.status_code != 200:
                raise Exception(
                    "Puzzle file api error when adding file '{}' on newly rendered puzzle".format(
                        name
                    )
                )



def cleanup_dir(path, keep_list):
    for (dirpath, dirnames, filenames) in os.walk(path, False):
        for filename in filenames:
            if filename not in keep_list:
                os.unlink(os.path.join(dirpath, filename))
        for dirname in dirnames:
            if dirname not in keep_list:
                rmtree(os.path.join(dirpath, dirname))


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
