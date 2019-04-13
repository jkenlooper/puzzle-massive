from __future__ import print_function
import os.path
import math

import sqlite3

from api.app import db
from api.database import rowify
from api.tools import loadConfig

FITS_MAPPING = {'top_path': {'x':0, 'y':-1},
                'right_path': {'x':1, 'y':0},
                'bottom_path': {'x':0, 'y':1},
                'left_path': {'x':-1, 'y':0},
                }


def migrate(db, puzzle):
    def get_offset_of_adjacent_pieces(piece, mask_width, piece_width):
        cur = db.cursor()
        offsets = {}

        x = piece['x']
        y = piece['y']
        t = mask_width - piece_width
        sides = [
            {'side':{
                (360, 0):'top_path',
                },
              'other_side':{
                (360, 0):'bottom_path',
                },
              'x':x,
              'y':((y+t) - mask_width)},
             {'side':{
               (360, 0):'right_path',
               },
              'other_side':{
                (360, 0):'left_path',
                },
              'x':((x-t) + mask_width),
              'y':y},
             {'side':{
               (360, 0):'bottom_path',
               },
              'other_side':{
                (360, 0):'top_path',
                },
              'x':x,
              'y':((y-t) + mask_width)},
             {'side':{
               (360, 0):'left_path',
               },
              'other_side':{
                (360, 0):'right_path',
                },
              'x':((x+t) - mask_width),
              'y':(y)},
            ]
        piece_alignment = (360, 0)

        query = """select * from Piece where (id != :id) and (puzzle = :puzzle) and ((top_path = :bottom_path) or (bottom_path = :top_path) or (right_path = :left_path) or (left_path = :right_path))"""
        (d, col_names) = rowify(cur.execute(query, piece).fetchall(), cur.description)
        for adjacent_piece in d:
            for s in sides:
                try:
                    if adjacent_piece[s['other_side'][piece_alignment]] == piece[s['side'][piece_alignment]]: # always check if the sides match
                        offset = {
                            'x': int(math.ceil(piece_width)*FITS_MAPPING[s['side'][piece_alignment]]['x']),
                            'y': int(math.ceil(piece_width)*FITS_MAPPING[s['side'][piece_alignment]]['y'])
                            }
                        offsets[adjacent_piece['id']] = '{x},{y}'.format(**offset)
                        break
                except KeyError:
                    continue

        cur.close()
        return offsets


    cur = db.cursor()
    query = """select * from Puzzle where (id = :puzzle)"""
    (result, col_names) = rowify(cur.execute(query, {'puzzle': puzzle}).fetchall(), cur.description)
    puzzle_data = result[0]
    mask_width = puzzle_data['mask_width']
    piece_width = puzzle_data['piece_width']

    # Set the immovable status based on this query
    query = """
    SELECT pc.parent, pc.id FROM Puzzle AS pz JOIN Piece AS pc ON (pz.id = pc.puzzle)
    WHERE pz.id = :puzzle AND col = 0 AND ROW = 0
    """
    (result, col_names) = rowify(cur.execute(query, {'puzzle': puzzle}).fetchall(), cur.description)
    if result:
        immovableGroup = int(result[0]['parent']) if result[0]['parent'] else int(result[0]['id'])
        #print "immovableGroup: {0}".format(immovableGroup)
    else:
        raise Exception


    query = """select * from Piece where (puzzle = :puzzle)"""
    (all_pieces, col_names) = rowify(cur.execute(query, {'puzzle': puzzle}).fetchall(), cur.description)
    cur.close()

    piece_updates = []

    for piece in all_pieces:
        #print('convert piece {id} for puzzle: {puzzle}'.format(**piece))
        offsets = get_offset_of_adjacent_pieces(piece, mask_width, piece_width)
        # Create the adjacent pieces string from offsets
        adjacent = ' '.join(map(lambda k, v: '{0}:{1}'.format(k, v), offsets.keys(), offsets.values()))
        #print offsets
        # Add Piece Properties
        pc = {
            #'x': piece['x'],
            #'y': piece['y'],
            #'r': piece['r'],
            #'rotate': piece['rotate'],
            'puzzle': puzzle,
            'id': piece.get('id'),
            'w': mask_width,
            'h': mask_width,
            'b': '0' if piece.get('bg') == 'dark' else '1',
            'adjacent': adjacent,
            'status': None,
            }

        pieceParent = piece.get('parent', None)

        # Determine immovable status based on parent
        if pieceParent != None and int(pieceParent) == immovableGroup:
            # status was never set in the past so patching it in here
            pc['status'] = 1
        piece_updates.append(pc)
    
    def each(pieces):
        for p in pieces:
            yield p

    cur = db.cursor()
    query = """update Piece set w = :w, h = :h, b = :b, adjacent = :adjacent, status = :status where id = :id and puzzle = :puzzle"""
    cur.executemany(query, each(piece_updates))
    db.commit()
    cur.close()

if __name__ == '__main__':
    #migrate('db', 264)
    #migrate('db', 255)
    #migrate('db', 10)
    import sys

    # Get the args from the worker and connect to the database
    config_file = sys.argv[1]
    config = loadConfig(config_file)

    db_file = config['CHILL_DATABASE_URI']
    db = sqlite3.connect(db_file)

    cur = db.cursor()
    query = """select * from Puzzle where status > 0"""
    (all_puzzles, col_names) = rowify(cur.execute(query).fetchall(), cur.description)
    cur.close()
    if all_puzzles:
        for puzzle in all_puzzles:
            print("{id} Migrating puzzle: {puzzle_id} with pieces: {pieces} and status: {status}".format(**puzzle))
            migrate(db, puzzle['id'])
