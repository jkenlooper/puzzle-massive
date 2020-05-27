from builtins import range
from random import randint

from flask import current_app, redirect
from flask_sse import sse

from api.app import db, redis_connection
from api.database import rowify, fetch_query_string
from api.constants import MAINTENANCE
from api.timeline import archive_and_clear
from api.jobs.convertPiecesToDB import transfer

query_select_puzzle_for_puzzle_id_and_status = """
select * from Puzzle where puzzle_id = :puzzle_id and status = :status
and strftime('%s', m_date) <= strftime('%s', 'now', '-7 hours');
"""

query_update_status_puzzle_for_puzzle_id = """
update Puzzle set status = :status, m_date = '' where puzzle_id = :puzzle_id;
"""

query_select_top_left_piece = """
select * from Piece where puzzle = :puzzle and row = 0 and col = 0;
"""


class Error(Exception):
    "Base exception for piece_reset"
    pass


class DataError(Error):
    def __init__(self, message):
        self.message = message


def reset_puzzle_pieces(puzzle):
    """
    Puzzles that are reset will reuse the same pieces as before and are
    not rerendered.
    """
    # TODO: Reset the redis puzzle token so players will be required to refresh
    # the browser if they had the puzzle open.

    cur = db.cursor()
    result = cur.execute(
        fetch_query_string("select_all_from_puzzle_for_id.sql"), {"id": puzzle},
    ).fetchall()
    if not result:
        cur.close()
        raise DataError("No puzzle found with that id.")

    (result, col_names) = rowify(result, cur.description)
    puzzle_data = result[0]

    # Update puzzle status to MAINTENANCE
    cur.execute(
        fetch_query_string("update_puzzle_status_for_puzzle.sql"),
        {"status": MAINTENANCE, "puzzle": puzzle_data["id"]},
    )
    db.commit()
    sse.publish(
        "status:{}".format(MAINTENANCE),
        channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_data["puzzle_id"]),
    )

    # Transfer any redis piece data out first.
    transfer(puzzle, cleanup=True, my_db=db)

    # TODO: archive the timeline
    # timeline ui should only show when the puzzle is in 'complete' status.
    archive_and_clear(
        puzzle, db, redis_connection, current_app.config.get("PUZZLE_ARCHIVE")
    )

    (x1, y1, x2, y2) = (0, 0, puzzle_data["table_width"], puzzle_data["table_height"])

    (result, col_names) = rowify(
        cur.execute(
            query_select_top_left_piece, {"puzzle": puzzle_data["id"]}
        ).fetchall(),
        cur.description,
    )
    topLeftPiece = result[0]
    allPiecesExceptTopLeft = list(range(0, puzzle_data["pieces"]))
    allPiecesExceptTopLeft.remove(topLeftPiece["id"])

    # Randomize piece x, y. Reset the parent
    for piece in allPiecesExceptTopLeft:
        x = randint(x1, x2)
        y = randint(y1, y2)
        cur.execute(
            "update Piece set x = :x, y = :y, parent = null, status = null where puzzle = :puzzle and id = :id",
            {"x": x, "y": y, "puzzle": puzzle, "id": piece},
        )

    # The caller should update the status of the puzzle to get it out of
    # MAINTENANCE mode.
    db.commit()
    cur.close()
