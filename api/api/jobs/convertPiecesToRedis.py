import sys
import os.path
import math
import time

from api.database import rowify
from api.tools import (
    loadConfig,
    get_db,
    get_redis_connection,
    formatPieceMovementString,
)
from api.constants import COMPLETED


def convert(puzzle):
    cur = db.cursor()

    query = """select * from Puzzle where (id = :puzzle)"""
    (result, col_names) = rowify(
        cur.execute(query, {"puzzle": puzzle}).fetchall(), cur.description
    )
    puzzle_data = result[0]

    query = """select * from Piece where (puzzle = :puzzle)"""
    (all_pieces, col_names) = rowify(
        cur.execute(query, {"puzzle": puzzle}).fetchall(), cur.description
    )

    # Create a pipe for buffering commands and disable atomic transactions
    pipe = redis_connection.pipeline(transaction=False)

    for piece in all_pieces:
        # print('convert piece {id} for puzzle: {puzzle}'.format(**piece))
        offsets = {}
        for (k, v) in [x.split(":") for x in piece.get("adjacent", "").split(" ")]:
            offsets[k] = v
        # print offsets
        # Add Piece Properties
        pc = {
            "x": piece["x"],
            "y": piece["y"],
            "r": piece["r"],  # mutable rotation of piece
            "rotate": piece["rotate"],  # immutable piece orientation
            "w": piece["w"],
            "h": piece["h"],
            "b": piece["b"],
            # The 's' is not set from the database 'status'. That is handled later
        }
        pc.update(offsets)
        pipe.hmset("pc:{puzzle}:{id}".format(**piece), pc)

        # Add Piece Group
        pieceParent = piece.get("parent", None)
        if pieceParent != None:
            pipe.sadd("pcg:{puzzle}:{parent}".format(**piece), piece["id"])
            pipe.hset("pc:{puzzle}:{id}".format(**piece), "g", piece["parent"])

        pieceStatus = piece.get("status", None)
        if pieceStatus != None:
            # print 'pieceStatus'
            # print pieceStatus
            # print("immovable piece: {id}".format(**piece))
            pieceStatus = int(
                pieceStatus
            )  # in case it's from the actual results of the query
            pipe.hset("pc:{puzzle}:{id}".format(**piece), "s", pieceStatus)
            if pieceStatus == 1:
                # Add Piece Fixed (immovable)
                pipe.sadd("pcfixed:{puzzle}".format(**locals()), piece["id"])
            elif pieceStatus == 2:
                # Add Piece Stacked
                pipe.sadd("pcstacked:{puzzle}".format(**locals()), piece["id"])

        # Add Piece x Set
        pipe.zadd("pcx:{puzzle}".format(**piece), {piece["id"]: piece["x"]})

        # Add Piece y Set
        pipe.zadd("pcy:{puzzle}".format(**piece), {piece["id"]: piece["y"]})

    # Add to the pcupdates sorted set
    pipe.zadd("pcupdates", {puzzle: int(time.time())})

    pipe.execute()
    cur.close()


if __name__ == "__main__":
    # Get the args from the worker and connect to the database
    config_file = sys.argv[1]
    config = loadConfig(config_file)

    db = get_db(config)
    redis_connection = get_redis_connection(config)

    # convert(db, 264)
    # convert(db, 255)

else:
    from api.app import db, redis_connection
