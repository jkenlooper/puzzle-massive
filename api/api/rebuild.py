from __future__ import absolute_import
from __future__ import division

from flask import current_app, redirect, abort, request
from flask.views import MethodView

from api.app import db, redis_connection

from api.database import rowify, fetch_query_string, delete_puzzle_resources
from api.constants import REBUILD, COMPLETED, QUEUE_REBUILD, PRIVATE

from api.user import user_id_from_ip, user_not_banned
from api.tools import deletePieceDataFromRedis, purge_route_from_nginx_cache

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
            current_app.secure_cookie.get("user")
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
                "/chill/site/front/{puzzle_id}/".format(puzzle_id=puzzle_id)
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

        if (
            puzzleData["permission"] == PRIVATE
            and puzzleData["original_puzzle_id"] == puzzleData["puzzle_id"]
        ):
            current_app.logger.warning(
                "Original puzzles that are private can not be rebuilt"
            )
            cur.close()
            abort(400)

        # The user points for rebuilding the puzzle is decreased by the piece
        # count for the puzzle. Use at least minimum piece count (20) points for
        # smaller puzzles.  Players that own a puzzle instance do not decrease
        # any points (dots) if the puzzle is complete.
        point_cost = max(
            current_app.config["MINIMUM_PIECE_COUNT"],
            min(
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
        cur.close()
        deletePieceDataFromRedis(redis_connection, puzzle, all_pieces)

        delete_puzzle_resources(
            puzzle_id,
            is_local_resource=not puzzleData["preview_full"].startswith("http")
            and not puzzleData["preview_full"].startswith("//"),
            exclude_regex=r"(original|preview_full).([^.]+\.)?jpg",
        )

        job = current_app.createqueue.enqueue(
            "api.jobs.pieceRenderer.render",
            [puzzleData],
            result_ttl=0,
            job_timeout="24h",
        )

        job = current_app.cleanupqueue.enqueue(
            "api.jobs.timeline_archive.archive_and_clear",
            puzzle,
            result_ttl=0,
            job_timeout="24h",
        )

        purge_route_from_nginx_cache(
            "/chill/site/front/{puzzle_id}/".format(puzzle_id=puzzle_id),
            current_app.config.get("PURGEURLLIST"),
        )

        return redirect("/chill/site/front/{puzzle_id}/".format(puzzle_id=puzzle_id))
