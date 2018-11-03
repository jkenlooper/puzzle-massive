import os
import json
import sys
from random import randint
import subprocess

import sqlite3
import redis
from PIL import Image
from piecemaker.base import JigsawPieceClipsSVG, Pieces
from piecemaker.adjacent import Adjacent

from api.database import rowify
from api.tools import loadConfig
from api.constants import (
        IN_RENDER_QUEUE,
        RENDERING,
        RENDERING_FAILED,
        IN_QUEUE,
        )

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

# Get the args from the worker and connect to the database
try:
    config_file = sys.argv[1]
    config = loadConfig(config_file)

    db_file = config['SQLITE_DATABASE_URI']
    db = sqlite3.connect(db_file)
except (IOError, IndexError):
    # Most likely being run from a test setup
    pass

redisConnection = redis.from_url('redis://localhost:6379/0/')


def handle_render_fail(job, exception, exception_func, traceback):
    """
    """
    cur = db.cursor()

    print("Handle render fail")
    for puzzle in job.args:
        print("set puzzle to fail status: {puzzle_id}".format(**puzzle))
        # Update Puzzle data
        cur.execute("update Puzzle set status = :RENDERING_FAILED where status = :RENDERING and id = :id;", {
            'RENDERING_FAILED': RENDERING_FAILED,
            'RENDERING': RENDERING,
            'id': puzzle['id']
            })
    db.commit()


def render(*args):
    """
    Render any puzzles that are in the render queue.
    Each puzzle should exist in the Puzzle db with the IN_RENDER_QUEUE status
    and have an original.jpg file.
    """
    # TODO: delete old piece properties if existing
    # TODO: delete old PuzzleFile for name if existing
    # TODO: update preview image in PuzzleFile?
    cur = db.cursor()

    for puzzle in args:
        print("Rendering puzzle: {puzzle_id}".format(**puzzle))
        # Set the status of the puzzle to rendering
        cur.execute("update Puzzle set status = :RENDERING where status = :IN_RENDER_QUEUE and id = :id", {
            'RENDERING': RENDERING,
            'IN_RENDER_QUEUE': IN_RENDER_QUEUE,
            'id': puzzle['id']
            })
        db.commit()

        result = cur.execute("select status from Puzzle where status = :RENDERING and id = :id", {
            'RENDERING': RENDERING,
            'id': puzzle['id']
            }).fetchone()
        if not result:
            print("Puzzle {puzzle_id} no longer in rendering status; skipping.".format(**puzzle))
            continue

        scaled_sizes = [100,]

        puzzle_dir = os.path.join(config['PUZZLE_RESOURCES'], puzzle['puzzle_id'])

        # Create the preview full
        im = Image.open(os.path.join(puzzle_dir, 'original.jpg')).copy()
        im.thumbnail(size=(384, 384))
        im.save(os.path.join(puzzle_dir, 'preview_full.jpg'))
        im.close()

        imagefile = os.path.join(puzzle_dir, 'original.jpg')

        im = Image.open(imagefile)
        (width, height) = im.size
        im.close()

        # Scale down puzzle image to avoid have pieces too big
        #min_pixels = (MIN_PIECE_SIZE * MIN_PIECE_SIZE) * int(puzzle['pieces'])
        max_pixels = min(MAX_PIXELS, (MAX_PIECE_SIZE * MAX_PIECE_SIZE) * int(puzzle['pieces']))
        im_pixels = width * height
        if im_pixels > max_pixels:
            resizedimagefile = os.path.join(puzzle_dir, 'resized-original.jpg')
            # The image is too big which would create piece sizes larger then the MAX_PIECE_SIZE
            # resize the image using image magick @
            subprocess.call(['convert', imagefile, '-resize', '{0}@'.format(max_pixels), '-strip', '-quality', '85%', resizedimagefile])
            im = Image.open(resizedimagefile)
            (width, height) = im.size
            im_pixels = width * height
            imagefile = resizedimagefile
            im.close()

        # Create svg lines
        jpc = JigsawPieceClipsSVG(
                width=width,
                height=height,
                pieces=int(puzzle['pieces']),
                minimum_piece_size=MIN_PIECE_SIZE)
        svgfile = os.path.join(puzzle_dir, 'lines.svg')
        f = open(svgfile, 'w')
        f.write(jpc.svg())
        f.close()


        # Create pieces
        piece_count = 0
        dimensions = {}
        for scale in scaled_sizes:
            scale = int(scale)
            scaled_dir = os.path.join(puzzle_dir, 'scale-%i' % scale)
            os.mkdir(scaled_dir)

            # max_pixels is 0 to prevent resizing, since this is handled before creating piece clips svg
            # Skip creating the svg files for each piece by setting vector to False (too memory intensive)
            pieces = Pieces(svgfile, imagefile, scaled_dir, scale=scale, max_pixels=0, vector=False)

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

        tw = dimensions[100]['table_width']
        th = dimensions[100]['table_height']

        # Update the table width/height
        cur.execute("update Puzzle set pieces = :pieces, table_width = :table_width, table_height = :table_height where id = :id", {
            'pieces': piece_count,
            'table_width': tw,
            'table_height': th,
            'id': puzzle['id']
            })
        db.commit()

        # Update the css file with dimensions for puzzle outline
        cssfile = open(os.path.join(puzzle_dir, 'scale-100', 'raster.css'), 'a')
        cssfile.write("[id=puzzle-outline]{{width:{width}px;height:{height}px;left:{left}px;top:{top}px;}}".format(width=pieces.width, height=pieces.height, left=int(round((tw - pieces.width) / 2)), top=int(round((th - pieces.height) / 2))))
        cssfile.close()


        # Get the top left piece by checking the bounding boxes
        top_left_piece = "0"
        minLeft = piece_bboxes[top_left_piece][0]
        minTop = piece_bboxes[top_left_piece][1]
        for key in piece_bboxes.keys():
            if piece_bboxes[key][0] <= minLeft and piece_bboxes[key][1] <= minTop:
                top_left_piece = key
                minLeft = piece_bboxes[key][0]
                minTop = piece_bboxes[key][1]
        top_left_piece = int(top_left_piece)

        piece_properties = []
        for i in range(0, piece_count):

            piece_properties.append({
                  "id": i,
                  "puzzle": puzzle['id'],
                  "x": randint(0,tw),
                  "y": randint(0,th),
                  "w": piece_bboxes[str(i)][2] - piece_bboxes[str(i)][0],
                  "h": piece_bboxes[str(i)][3] - piece_bboxes[str(i)][1],
                  "r": 0,
                  "rotate": 0,
                  "row": -1, # deprecated
                  "col": -1, # deprecated
                  "s": 0, # side
                  "g": None, # parent
                  "b": 2, # TODO: will need to be either 0 for dark or 1 for light
                  "status": None
                })

        # Set the top left piece to the top left corner and make it immovable
        piece_properties[top_left_piece]["x"] = int(round((tw - pieces.width) / 2))
        piece_properties[top_left_piece]["y"] = int(round((th - pieces.height) / 2))
        piece_properties[top_left_piece]["status"] = 1
        piece_properties[top_left_piece]["g"] = top_left_piece
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
        f = open(os.path.join(puzzle_dir, 'index.json'), 'w')
        json.dump(data, f)
        f.close()

        # Create adjacent pieces
        adjacent_pieces = None
        if False: #TODO: Use the overlapping masks approach when using a custom cut lines
            first_scaled_dir = os.path.join(puzzle_dir, 'scale-%i' % scaled_sizes[0])
            adjacent = Adjacent(first_scaled_dir, by_overlap=True)
            adjacent_pieces = adjacent.adjacent_pieces
        else: # Find adjacent pieces by bounding boxes only and skip corners
            first_scaled_dir = os.path.join(puzzle_dir, 'scale-%i' % scaled_sizes[0])
            adjacent = Adjacent(first_scaled_dir, by_overlap=False)
            adjacent_pieces = adjacent.adjacent_pieces
            filtered_adjacent_pieces = {}

            # filter out the corner adjacent pieces
            for target_id, target_adjacent_list in adjacent_pieces.items():
                target_bbox = piece_bboxes[target_id] # [0, 0, 499, 500]
                target_center_x = target_bbox[0] + int(round((target_bbox[2] - target_bbox[0]) / 2))
                target_center_y = target_bbox[1] + int(round((target_bbox[3] - target_bbox[1]) / 2))
                filtered_adjacent_list = []
                for adjacent_id in target_adjacent_list:
                    adjacent_bbox = piece_bboxes[adjacent_id] # [0, 347, 645, 996]
                    left = (adjacent_bbox[0] < target_center_x) and (adjacent_bbox[2] < target_center_x)
                    top = (adjacent_bbox[1] < target_center_y) and (adjacent_bbox[3] < target_center_y)
                    right = (adjacent_bbox[0] > target_center_x) and (adjacent_bbox[2] > target_center_x)
                    bottom = (adjacent_bbox[1] > target_center_y) and (adjacent_bbox[3] > target_center_y)

                    if (top and left) or (top and right) or (bottom and left) or (bottom and right):
                        loc = []
                        if (top and left):
                            loc.append("top left")
                        if (top and right):
                            loc.append("top right")
                        if (bottom and left):
                            loc.append("bottom left")
                        if (bottom and right):
                            loc.append("bottom right")
                        #print("adjacent piece: {0} is {2} corner piece of {1}".format(adjacent_id, target_id, loc))
                        #print("adjacent bbox: {0}".format(adjacent_bbox))
                        #print("target bbox: {0}".format(target_bbox))
                    else:
                        filtered_adjacent_list.append(adjacent_id)

                filtered_adjacent_pieces[target_id] = filtered_adjacent_list
            adjacent_pieces = filtered_adjacent_pieces
            #print(filtered_adjacent_pieces)
            #for f, g in filtered_adjacent_pieces.items():
            #    print("{0} with {1} adjacent pieces: {2}".format(f, len(g), g))

        f = open(os.path.join(puzzle_dir, 'adjacent.json'), 'w')
        json.dump(adjacent_pieces, f)
        f.close()

        # Create adjacent offsets for the scale
        for pc in piece_properties:
            origin_x = piece_bboxes[str(pc['id'])][0]
            origin_y = piece_bboxes[str(pc['id'])][1]
            offsets = {}
            for adj_pc in adjacent_pieces[str(pc['id'])]:
                x = piece_bboxes[adj_pc][0] - origin_x
                y = piece_bboxes[adj_pc][1] - origin_y
                offsets[adj_pc] = '{x},{y}'.format(x=x, y=y)
            adjacent_str = ' '.join(map(lambda k, v: '{0}:{1}'.format(k, v), offsets.keys(), offsets.values()))
            pc['adjacent'] = adjacent_str

        # Commit the piece properties and puzzle resources
        # row and col are really only useful for determining the top left piece when resetting puzzle
        for pc in piece_properties:
            cur.execute("""
                insert or ignore into Piece (id, x, y, r, w, h, b, adjacent, rotate, row, col, status, parent, puzzle) values (
              :id, :x, :y, :r, :w, :h, :b, :adjacent, :rotate, :row, :col, :status, :g, :puzzle
                );""", pc)

        # Update Puzzle data
        cur.execute("update Puzzle set status = :status where id = :id", {
            'status': IN_QUEUE,
            'id': puzzle['id']
            })
        cur.execute(insert_puzzle_file, {
            'puzzle': puzzle['id'],
            'name': 'pieces',
            'url': '/resources/{puzzle_id}/scale-100/raster.png'.format(**puzzle)
            })
        cur.execute(insert_puzzle_file, {
            'puzzle': puzzle['id'],
            'name': 'pzz',
            'url': '/resources/{puzzle_id}/scale-100/raster.css'.format(**puzzle)
            })
        db.commit()

        cleanup(puzzle['puzzle_id'])

def cleanup(puzzle_id):
    whitelist = [
        'original.jpg',
        'preview_full.jpg',
        'resized-original.jpg',
        'scale-100',
        'raster.css',
        'raster.png'
    ]
    puzzle_dir = os.path.join(config['PUZZLE_RESOURCES'], puzzle_id)
    for (dirpath, dirnames, filenames) in os.walk(puzzle_dir, False):
        for filename in filenames:
            if filename not in whitelist:
                os.unlink(os.path.join(dirpath, filename))
        for dirname in dirnames:
            if dirname not in whitelist:
                os.rmdir(os.path.join(dirpath, dirname))


if __name__ == '__main__':
    render()
