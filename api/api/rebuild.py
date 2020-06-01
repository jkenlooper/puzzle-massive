from __future__ import absolute_import
from __future__ import division
from past.utils import old_div
import os
from random import randint

from flask import current_app, redirect, make_response, abort, request
from flask.views import MethodView
from PIL import Image

from .app import db, redis_connection

from .database import rowify, fetch_query_string
from .constants import REBUILD, COMPLETED, QUEUE_REBUILD
from .timeline import archive_and_clear
from .user import user_id_from_ip, user_not_banned
from .jobs.convertPiecesToRedis import convert
from .tools import deletePieceDataFromRedis

# From pieceRenderer
MIN_PIECE_SIZE = 64


class PuzzlePiecesRebuildView(MethodView):
    """
    When a puzzle is complete allow rebuilding it.
    """

    decorators = [user_not_banned]

    def post(self):
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        puzzle_id = args.get("puzzle_id")
        if not puzzle_id:
            abort(400)

        # Check pieces arg
        try:
            pieces = int(args.get("pieces", current_app.config["MINIMUM_PIECE_COUNT"]))
        except ValueError as err:
            abort(400)
        if pieces < current_app.config["MINIMUM_PIECE_COUNT"]:
            abort(400)

        user = int(
            current_app.secure_cookie.get(u"user")
            or user_id_from_ip(request.headers.get("X-Real-IP"))
        )

        cur = db.cursor()
        result = cur.execute(
            fetch_query_string(
                "select_puzzle_for_puzzle_id_and_status_and_not_recent.sql"
            ),
            {"puzzle_id": puzzle_id, "status": COMPLETED},
        ).fetchall()
        if not result:
            # Puzzle does not exist or is not completed status.
            # Reload the page as the status may have been changed.
            cur.close()
            return redirect(
                "/chill/site/puzzle/{puzzle_id}/".format(puzzle_id=puzzle_id)
            )

        (result, col_names) = rowify(result, cur.description)
        puzzleData = result[0]
        puzzle = puzzleData["id"]

        userCanRebuildPuzzle = cur.execute(
            fetch_query_string("select-user-rebuild-puzzle-prereq.sql"),
            {"user": user, "puzzle": puzzle, "pieces": pieces},
        ).fetchall()
        if not userCanRebuildPuzzle:
            cur.close()
            abort(400)

        original_puzzle_id = puzzleData["original_puzzle_id"]
        # Get the adjusted piece count depending on the size of the original and
        # the minimum piece size.
        original_puzzle_dir = os.path.join(
            current_app.config["PUZZLE_RESOURCES"], original_puzzle_id
        )
        # TODO: get path of original.jpg via the PuzzleFile query
        # TODO: use requests.get to get original.jpg and run in another thread
        imagefile = os.path.join(original_puzzle_dir, "original.jpg")
        im = Image.open(imagefile)
        (width, height) = im.size
        im.close()
        max_pieces_that_will_fit = int(
            (old_div(width, MIN_PIECE_SIZE)) * (old_div(height, MIN_PIECE_SIZE))
        )

        # The user points for rebuilding the puzzle is decreased by the piece
        # count for the puzzle. Use at least 200 points for smaller puzzles.
        # Players that own a puzzle instance do not decrease any points (dots)
        # if the puzzle is complete.
        point_cost = max(
            current_app.config["MINIMUM_PIECE_COUNT"],
            min(
                max_pieces_that_will_fit,
                pieces,
                current_app.config["MAX_POINT_COST_FOR_REBUILDING"],
            ),
        )
        if not (
            puzzleData["owner"] == user
            and puzzleData["puzzle_id"] == puzzleData["original_puzzle_id"]
        ):
            cur.execute(
                fetch_query_string("decrease-user-points.sql"),
                {"user": user, "points": point_cost},
            )

        # Update puzzle status to be REBUILD and change the piece count
        cur.execute(
            fetch_query_string("update_status_puzzle_for_puzzle_id.sql"),
            {
                "puzzle_id": puzzle_id,
                "status": REBUILD,
                "pieces": pieces,
                "queue": QUEUE_REBUILD,
            },
        )
        puzzleData["status"] = REBUILD
        puzzleData["pieces"] = pieces

        db.commit()

        # Delete any piece data from redis since it is no longer needed.
        (all_pieces, col_names) = rowify(
            cur.execute(
                fetch_query_string("select_all_piece_ids_for_puzzle.sql"),
                {"puzzle": puzzle},
            ).fetchall(),
            cur.description,
        )
        deletePieceDataFromRedis(redis_connection, puzzle, all_pieces)

        job = current_app.createqueue.enqueue_call(
            func="api.jobs.pieceRenderer.render",
            args=([puzzleData]),
            result_ttl=0,
            timeout="24h",
        )

        archive_and_clear(puzzle)

        cur.close()
        db.commit()

        return redirect("/chill/site/puzzle/{puzzle_id}/".format(puzzle_id=puzzle_id))
