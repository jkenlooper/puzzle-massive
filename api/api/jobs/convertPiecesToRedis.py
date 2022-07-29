"""convertPiecesToRedis.py

Usage: convertPiecesToRedis.py [--config <file>] [--cleanup]
       convertPiecesToRedis.py --help

Options:
  -h --help         Show this screen.
  --config <file>   Set config file. [default: site.cfg]
"""
import time
from docopt import docopt

from api.app import redis_connection, db, make_app
from api.database import rowify
from api.tools import (
    loadConfig,
)


def convert(puzzle):
    cur = db.cursor()

    query = """select * from Piece where (puzzle = :puzzle)"""
    (all_pieces, col_names) = rowify(
        cur.execute(query, {"puzzle": puzzle}).fetchall(), cur.description
    )

    pzm_puzzle_key = "pzm:{puzzle}".format(puzzle=puzzle)
    # Bump the pzm id when preparing to mutate the puzzle.
    puzzle_mutation_id = redis_connection.incr(pzm_puzzle_key)

    # Create a pipe for buffering commands to load up piece data
    with redis_connection.pipeline(transaction=True) as pipe:
        for piece in all_pieces:
            pc_puzzle_piece_key = "pc:{puzzle}:{piece}".format(
                puzzle=puzzle, piece=piece["id"]
            )
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
                # The 'g' property for piece group is set depending on piece["parent"]
                # The 's' is not set from the database 'status'. That is handled later
            }
            pc.update(offsets)
            pipe.hmset(pc_puzzle_piece_key, pc)

            # Add Piece Group
            pieceParent = piece.get("parent", None)
            if pieceParent is not None:
                pipe.sadd(
                    "pcg:{puzzle}:{parent}".format(
                        puzzle=puzzle, parent=piece["parent"]
                    ),
                    piece["id"],
                )
                pipe.hset(pc_puzzle_piece_key, "g", piece["parent"])

            pieceStatus = piece.get("status", None)
            if pieceStatus is not None:
                # print 'pieceStatus'
                # print pieceStatus
                # print("immovable piece: {id}".format(**piece))
                pieceStatus = int(
                    pieceStatus
                )  # in case it's from the actual results of the query
                if pieceStatus == 1:
                    # Add Piece Fixed (immovable)
                    pipe.sadd("pcfixed:{puzzle}".format(puzzle=puzzle), piece["id"])
                # Enforcer will reasses the stacked piece status (pcstacked) if that rule has been enabled.
                elif pieceStatus == 2:
                    # Add Piece Stacked
                    pipe.sadd("pcstacked:{puzzle}".format(puzzle=puzzle), piece["id"])

        # Add to the pcupdates sorted set
        pipe.zadd("pcupdates", {puzzle: int(time.time())})

        pipe.execute()
    cur.close()


if __name__ == "__main__":
    args = docopt(__doc__)
    config_file = args["--config"]
    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")
    app = make_app(config=config_file, cookie_secret=cookie_secret)

    with app.app_context():
        pass
        # convert(db, 264)
        # convert(db, 255)
