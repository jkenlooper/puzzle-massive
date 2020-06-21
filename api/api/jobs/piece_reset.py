from builtins import range
from random import randint

from flask import current_app, redirect
from flask_sse import sse
import requests

from api.app import db, redis_connection
from api.database import rowify, fetch_query_string
from api.constants import MAINTENANCE, RENDERING_FAILED, ACTIVE
from api.jobs.timeline_archive import archive_and_clear
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
    r = requests.patch(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle_data["puzzle_id"],
        ),
        json={"status": MAINTENANCE},
    )
    if r.status_code != 200:
        raise Exception("Puzzle details api error")
    sse.publish(
        "status:{}".format(MAINTENANCE),
        channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_data["puzzle_id"]),
    )

    # Transfer any redis piece data out first.
    transfer(puzzle, cleanup=True)

    # timeline ui should only show when the puzzle is in 'complete' status.
    archive_and_clear(puzzle)

    (x1, y1, x2, y2) = (0, 0, puzzle_data["table_width"], puzzle_data["table_height"])

    (result, col_names) = rowify(
        cur.execute(
            query_select_top_left_piece, {"puzzle": puzzle_data["id"]}
        ).fetchall(),
        cur.description,
    )
    cur.close()
    topLeftPiece = result[0]
    allPiecesExceptTopLeft = list(range(0, puzzle_data["pieces"]))
    allPiecesExceptTopLeft.remove(topLeftPiece["id"])

    # Randomize piece x, y. Reset the parent
    new_piece_properties = []
    for piece in allPiecesExceptTopLeft:
        x = randint(x1, x2)
        y = randint(y1, y2)
        new_piece_properties.append(
            {"x": x, "y": y, "parent": None, "status": None, "id": piece}
        )

    current_app.logger.debug(new_piece_properties)
    r = requests.patch(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/pieces/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle_data["puzzle_id"],
        ),
        json={"piece_properties": new_piece_properties},
    )
    if r.status_code != 200:
        raise Exception(
            "Puzzle pieces api error. Failed to patch pieces. {}".format(r.json())
        )
    # The caller should update the status of the puzzle to get it out of
    # MAINTENANCE mode.


def reset_puzzle_pieces_and_handle_errors(puzzle):
    cur = db.cursor()
    result = cur.execute(
        fetch_query_string("select_all_from_puzzle_for_id.sql"), {"id": puzzle},
    ).fetchall()
    if not result:
        cur.close()
        raise DataError("No puzzle found with that id.")

    (result, col_names) = rowify(result, cur.description)
    puzzle_data = result[0]
    cur.close()

    try:
        reset_puzzle_pieces(puzzle)
    except Error as err:
        # Update puzzle status to RENDERING_FAILED
        r = requests.patch(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                HOSTAPI=current_app.config["HOSTAPI"],
                PORTAPI=current_app.config["PORTAPI"],
                puzzle_id=puzzle_data["puzzle_id"],
            ),
            json={"status": RENDERING_FAILED},
        )
        sse.publish(
            "status:{}".format(RENDERING_FAILED),
            channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_data["puzzle_id"]),
        )
        if r.status_code != 200:
            raise Exception("Puzzle details api error")

    # Update puzzle status to ACTIVE and sse publish
    r = requests.patch(
        "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
            HOSTAPI=current_app.config["HOSTAPI"],
            PORTAPI=current_app.config["PORTAPI"],
            puzzle_id=puzzle_data["puzzle_id"],
        ),
        json={"status": ACTIVE},
    )
    sse.publish(
        "status:{}".format(ACTIVE),
        channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_data["puzzle_id"]),
    )
    if r.status_code != 200:
        raise Exception("Puzzle details api error")
