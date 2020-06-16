# /newapi/puzzle-instance/
import os

from flask import current_app, redirect, make_response, abort, request
from flask.views import MethodView

from api.app import db
from api.database import rowify, fetch_query_string, generate_new_puzzle_id
from api.user import user_id_from_ip, user_not_banned
from api.tools import check_bg_color
from api.jobs import piece_forker
from api.constants import (
    PUBLIC,
    PRIVATE,
    ACTIVE,
    BUGGY_UNLISTED,
    IN_QUEUE,
    COMPLETED,
    FROZEN,
    REBUILD,
    IN_RENDER_QUEUE,
    MAINTENANCE,
    RENDERING,
    CLASSIC,
    QUEUE_NEW,
)


class CreatePuzzleInstanceView(MethodView):
    """
    Handle a form submission to create a new puzzle instance from an existing puzzle.
    The player needs to have an available puzzle instance slot.
    """

    decorators = [user_not_banned]

    def post(self):
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # Check pieces arg
        try:
            pieces = int(args.get("pieces", current_app.config["MINIMUM_PIECE_COUNT"]))
        except ValueError as err:
            abort(400)
        if pieces < current_app.config["MINIMUM_PIECE_COUNT"]:
            abort(400)

        bg_color = check_bg_color(args.get("bg_color", "#808080")[:50])

        # Check description
        instance_description = args.get("instance_description", "")

        # Check puzzle_id
        source_puzzle_id = args.get("puzzle_id")
        if not source_puzzle_id:
            abort(400)

        # Check fork
        fork = int(args.get("fork", "0"))
        if fork not in (0, 1):
            abort(400)
        fork = bool(fork == 1)

        # Check permission
        permission = int(args.get("permission", PUBLIC))
        if permission not in (PUBLIC, PRIVATE):
            abort(400)
        if fork:
            # All copies of puzzles are unlisted
            permission = PRIVATE

        user = int(
            current_app.secure_cookie.get(u"user")
            or user_id_from_ip(request.headers.get("X-Real-IP"))
        )

        cur = db.cursor()

        # The user should have
        # 2400 or more dots (points)
        # TODO: this could be configurable per site or for other reasons.
        # userHasEnoughPoints = cur.execute(fetch_query_string("select-minimum-points-for-user.sql"), {'user': user, 'points': 2400}).fetchall()
        # if not userHasEnoughPoints:
        #    abort(400)

        # An available instance slot
        result = cur.execute(
            fetch_query_string("select-available-user-puzzle-slot-for-player.sql"),
            {"player": user},
        ).fetchone()[0]
        userHasAvailablePuzzleInstanceSlot = bool(result)
        if not userHasAvailablePuzzleInstanceSlot:
            cur.close()
            db.commit()
            abort(400)

        # Check if puzzle is valid to be a new puzzle instance
        if not fork:
            # Creating a new puzzle instance
            result = cur.execute(
                fetch_query_string("select-valid-puzzle-for-new-puzzle-instance.sql"),
                {
                    "puzzle_id": source_puzzle_id,
                    "ACTIVE": ACTIVE,
                    "IN_QUEUE": IN_QUEUE,
                    "COMPLETED": COMPLETED,
                    "FROZEN": FROZEN,
                    "REBUILD": REBUILD,
                    "IN_RENDER_QUEUE": IN_RENDER_QUEUE,
                    "RENDERING": RENDERING,
                },
            ).fetchall()
            if not result:
                # Puzzle does not exist or is not a valid puzzle to create instance from.
                cur.close()
                db.commit()
                abort(400)
        else:
            # Creating a copy of existing puzzle pieces (forking)
            result = cur.execute(
                fetch_query_string(
                    "select-valid-puzzle-for-new-puzzle-instance-fork.sql"
                ),
                {
                    "puzzle_id": source_puzzle_id,
                    "ACTIVE": ACTIVE,
                    "IN_QUEUE": IN_QUEUE,
                    "COMPLETED": COMPLETED,
                    "FROZEN": FROZEN,
                },
            ).fetchall()
            if not result:
                # Puzzle does not exist or is not a valid puzzle to create instance from.
                cur.close()
                db.commit()
                abort(400)

        (result, col_names) = rowify(result, cur.description)
        source_puzzle_data = result[0]

        puzzle_id = generate_new_puzzle_id(source_puzzle_data["name"])

        # Create puzzle dir
        if not fork:
            puzzle_dir = os.path.join(
                current_app.config.get("PUZZLE_RESOURCES"), puzzle_id
            )
            os.mkdir(puzzle_dir)

        if not fork:
            d = {
                "puzzle_id": puzzle_id,
                "pieces": pieces,
                "name": source_puzzle_data["name"],
                "link": source_puzzle_data["link"],
                "description": source_puzzle_data["description"]
                if not instance_description
                else instance_description,
                "bg_color": bg_color,
                "owner": user,
                "queue": QUEUE_NEW,
                "status": IN_RENDER_QUEUE,
                "permission": permission,
            }
            cur.execute(
                fetch_query_string("insert_puzzle.sql"), d,
            )
        else:
            d = {
                "puzzle_id": puzzle_id,
                "pieces": source_puzzle_data["pieces"],
                "rows": source_puzzle_data["rows"],
                "cols": source_puzzle_data["cols"],
                "piece_width": source_puzzle_data["piece_width"],
                "mask_width": source_puzzle_data["mask_width"],
                "table_width": source_puzzle_data["table_width"],
                "table_height": source_puzzle_data["table_height"],
                "name": source_puzzle_data["name"],
                "link": source_puzzle_data["link"],
                "description": source_puzzle_data["description"]
                if not instance_description
                else instance_description,
                "bg_color": bg_color,
                "owner": user,
                "queue": QUEUE_NEW,
                "status": MAINTENANCE,
                "permission": permission,  # All copies of puzzles are unlisted
            }
            cur.execute(
                fetch_query_string("insert_puzzle_instance_copy.sql"), d,
            )
        db.commit()

        result = cur.execute(
            fetch_query_string("select-all-from-puzzle-by-puzzle_id.sql"),
            {"puzzle_id": puzzle_id},
        ).fetchall()
        if not result:
            cur.close()
            db.commit()
            abort(500)

        (result, col_names) = rowify(result, cur.description)
        puzzle_data = result[0]
        puzzle = puzzle_data["id"]

        classic_variant = cur.execute(
            fetch_query_string("select-puzzle-variant-id-for-slug.sql"),
            {"slug": CLASSIC},
        ).fetchone()[0]
        cur.execute(
            fetch_query_string("insert-puzzle-instance.sql"),
            {
                "original": source_puzzle_data["id"],
                "instance": puzzle,
                "variant": classic_variant,
            },
        )

        cur.execute(
            fetch_query_string("fill-user-puzzle-slot.sql"),
            {"player": user, "puzzle": puzzle},
        )

        db.commit()
        cur.close()

        if not fork:
            job = current_app.createqueue.enqueue_call(
                func="api.jobs.pieceRenderer.render",
                args=([puzzle_data]),
                result_ttl=0,
                timeout="24h",
            )
        else:
            # Copy existing puzzle
            # TODO: switch to using requests
            job = current_app.cleanupqueue.enqueue_call(
                func="api.jobs.piece_forker.fork_puzzle_pieces",
                args=([source_puzzle_data, puzzle_data]),
                result_ttl=0,
            )

        return redirect("/chill/site/front/{0}/".format(puzzle_id), code=303)
