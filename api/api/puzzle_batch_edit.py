"Admin Puzzle Edit"
import os

from flask import current_app, redirect, request, make_response, abort
from flask.views import MethodView

from api.app import db, redis_connection
from api.database import rowify, fetch_query_string, delete_puzzle_resources
from api.timeline import delete_puzzle_timeline
from api.tools import purge_route_from_nginx_cache
from api.constants import (
    ACTIVE,
    IN_QUEUE,
    COMPLETED,
    FROZEN,
    NEEDS_MODERATION,
    FAILED_LICENSE,
    NO_ATTRIBUTION,
    IN_RENDER_QUEUE,
    REBUILD,
    RENDERING,
    DELETED_LICENSE,
    DELETED_INAPT,
    DELETED_OLD,
    DELETED_REQUEST,
    PRIVATE,
)


ACTIONS = ("approve", "rebuild", "reject", "delete", "edit", "tag")


class AdminPuzzleBatchEditView(MethodView):
    """
    Handle editing a batch of puzzles.
    """

    def post(self):
        "Route is protected by basic auth in nginx"
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # TODO: Check user to see if role matches?
        # user = current_app.secure_cookie.get(u'user')
        # if not user:
        #     abort(403)

        # Verify args
        action = args.get("action")
        if action not in ACTIONS:
            abort(400)

        reject = args.get("reject")
        if action == "reject" and reject not in ("license", "attribution"):
            abort(400)

        delete = args.get("delete")
        if action == "delete" and delete not in ("license", "inapt", "old", "request"):
            abort(400)

        edit = args.get("edit")
        if action == "edit" and edit not in ("private",):
            abort(400)

        # abort if tag value not set
        tag = args.get("tag")
        if action == "tag" and not tag:
            abort(400)

        puzzle_ids = request.form.getlist("montage_puzzle_id")
        if len(puzzle_ids) == 0:
            abort(400)
        if not isinstance(puzzle_ids, list):
            puzzle_ids = [puzzle_ids]

        cur = db.cursor()
        status = None

        if action == "approve":
            status = IN_RENDER_QUEUE

        if action == "rebuild":
            status = REBUILD

        if action == "reject":
            if reject == "license":
                status = FAILED_LICENSE
            elif reject == "attribution":
                status = NO_ATTRIBUTION

        if action == "delete":
            if delete == "license":
                status = DELETED_LICENSE
            elif delete == "inapt":
                status = DELETED_INAPT
            elif delete == "old":
                status = DELETED_OLD
            elif delete == "request":
                status = DELETED_REQUEST

            for puzzle_id in puzzle_ids:
                result = cur.execute(
                    fetch_query_string("select-puzzle-details-for-puzzle_id.sql"),
                    {"puzzle_id": puzzle_id},
                ).fetchall()
                (result, col_names) = rowify(result, cur.description)
                puzzle_details = result[0]

                delete_puzzle_resources(puzzle_id, is_local_resource=not puzzle_details["url"].startswith("http") or not puzzle_details["url"].startswith("//"))
                id = puzzle_details["id"]
                # current_app.logger.info('deleting puzzle resources for id {}'.format(id))
                cur.execute(
                    fetch_query_string("delete_puzzle_file_for_puzzle.sql"),
                    {"puzzle": id},
                )
                cur.execute(
                    fetch_query_string("delete_piece_for_puzzle.sql"), {"puzzle": id}
                )

                msg = delete_puzzle_timeline(puzzle_id)
                if msg.get("status_code") >= 400:
                    current_app.logger.error(msg.get("msg"))
                    current_app.logger.error(
                        f"Failed delete of puzzle timeline for puzzle_id {puzzle_id}"
                    )

                cur.execute(
                    fetch_query_string("remove-puzzle-from-all-user-puzzle-slots.sql"),
                    {"puzzle": id},
                )

            db.commit()

        if action == "edit":
            if edit == "private":

                def each(puzzle_ids):
                    for puzzle_id in puzzle_ids:
                        yield {"puzzle_id": puzzle_id, "permission": PRIVATE}

                cur.executemany(
                    fetch_query_string("update_puzzle_permission_for_puzzle_id.sql"),
                    each(puzzle_ids),
                )
                db.commit()

        def each(puzzle_ids):
            for puzzle_id in puzzle_ids:
                yield {"puzzle_id": puzzle_id, "status": status}

        if status is not None:
            cur.executemany(
                fetch_query_string("update_puzzle_status_for_puzzle_id.sql"),
                each(puzzle_ids),
            )
            db.commit()

        for puzzle_id in puzzle_ids:
            purge_route_from_nginx_cache(
                "/chill/site/front/{puzzle_id}/".format(puzzle_id=puzzle_id),
                current_app.config.get("PURGEURLLIST"),
            )

        if action in ("approve", "rebuild"):
            puzzles = rowify(
                cur.execute(
                    fetch_query_string("select-puzzles-in-render-queue.sql"),
                    {"IN_RENDER_QUEUE": IN_RENDER_QUEUE, "REBUILD": REBUILD},
                ).fetchall(),
                cur.description,
            )[0]
            print("found {0} puzzles to render or rebuild".format(len(puzzles)))

            # push each puzzle to artist job queue
            for puzzle in puzzles:
                job = current_app.createqueue.enqueue(
                    "api.jobs.pieceRenderer.render",
                    [puzzle],
                    result_ttl=0,
                    job_timeout="24h",
                )

        # TODO: if action in ('reject', 'delete'): #Also apply to any puzzle instances

        cur.close()
        return redirect("/chill/site/admin/puzzle/", code=303)
