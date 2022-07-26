from flask import current_app, request, abort, json, make_response
from flask.views import MethodView
from flask_sse import sse

from api.app import db, redis_connection
from api.user import user_id_from_ip, user_not_banned
from api.jobs import piece_reset
from api.database import fetch_query_string, rowify, delete_puzzle_resources
from api.timeline import delete_puzzle_timeline
from api.tools import purge_route_from_nginx_cache
from api.constants import (
    DELETED_REQUEST,
    FROZEN,
    BUGGY_UNLISTED,
    ACTIVE,
    COMPLETED,
    IN_QUEUE,
    RENDERING_FAILED,
    REBUILD,
    IN_RENDER_QUEUE,
    MAINTENANCE,
    QUEUE_WINNING_BID,
    PRIVATE,
    PUBLIC,
)

ORIGINAL_ACTIONS = ("bump",)

INSTANCE_ACTIONS = ("delete", "freeze", "unfreeze", "reset")


class PuzzleInstanceDetailsView(MethodView):
    """"""

    decorators = [user_not_banned]

    def get_delete_prereq(self, puzzleData):
        """
        The delete penalty is to limit how many puzzles a player can delete when
        they are not complete.  The limit is needed because it doesn't cost any
        dots to create a puzzle instance.
        For puzzles that have no or an older modified date, the delete penalty
        is waived.
        """
        delete_penalty = 0
        can_delete = True
        delete_disabled_message = ""
        if not puzzleData["is_owner"]:
            can_delete = False
        else:
            if puzzleData["status"] not in (
                COMPLETED,
                RENDERING_FAILED,
                BUGGY_UNLISTED,
                MAINTENANCE,
            ):
                delete_penalty = min(
                    current_app.config["MAX_POINT_COST_FOR_DELETING"],
                    max(
                        current_app.config["MINIMUM_PIECE_COUNT"], puzzleData["pieces"]
                    ),
                )
                # Handle issue if user_points is None
                can_delete = int(puzzleData["user_points"] or "0") >= delete_penalty
                # Waive the delete penalty if the m_date for the puzzle is old
                if not puzzleData["m_date"]:
                    # Puzzles without an m_date may have been created before the
                    # change to pieceRenderer that set an initial m_date or the
                    # puzzle failed to render.
                    can_delete = True
                    delete_penalty = -1
                elif puzzleData["is_old"]:
                    # A puzzle with an older m_date should be allowed to be deleted
                    # without the delete penalty.
                    can_delete = True
                    delete_penalty = -1
                if not can_delete:
                    delete_disabled_message = "Not enough dots to delete this puzzle"
        return (delete_penalty, can_delete, delete_disabled_message)

    def patch(self, puzzle_id):
        ip = request.headers.get("X-Real-IP")
        user = int(current_app.secure_cookie.get("user") or user_id_from_ip(ip))

        # validate the args and headers
        args = {}
        xhr_data = request.get_json()
        if xhr_data:
            args.update(xhr_data)
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # Verify args
        action = args.get("action")
        if action not in INSTANCE_ACTIONS:
            abort(400)

        cur = db.cursor()

        # validate the puzzle_id
        result = cur.execute(
            fetch_query_string("select-puzzle-details-for-puzzle_id.sql"),
            {"puzzle_id": puzzle_id},
        ).fetchall()
        if not result:
            # 400 if puzzle does not exist
            err_msg = {
                "msg": "No puzzle found",
            }
            cur.close()
            return make_response(json.jsonify(err_msg), 400)
        (result, col_names) = rowify(result, cur.description)
        puzzleData = result[0]

        if puzzleData["owner"] != user or puzzleData["is_original"]:
            cur.close()
            abort(400)

        if puzzleData["status"] not in (
            FROZEN,
            ACTIVE,
            COMPLETED,
            BUGGY_UNLISTED,
            RENDERING_FAILED,
            REBUILD,
            IN_RENDER_QUEUE,
            MAINTENANCE,
        ):
            cur.close()
            abort(400)

        if action in ("freeze", "unfreeze") and puzzleData["status"] not in (
            FROZEN,
            BUGGY_UNLISTED,
            ACTIVE,
        ):
            cur.close()
            abort(400)

        response = {}

        if action == "delete":

            (
                delete_penalty,
                can_delete,
                delete_disabled_message,
            ) = self.get_delete_prereq(puzzleData)
            if not can_delete:
                response = {"msg": delete_disabled_message}
                cur.close()
                return make_response(json.jsonify(response), 400)

            if delete_penalty > 0:
                cur.execute(
                    fetch_query_string("decrease-user-points.sql"),
                    {"user": user, "points": delete_penalty},
                )

            delete_puzzle_resources(
                puzzle_id,
                is_local_resource=not puzzleData["url"].startswith("http")
                and not puzzleData["url"].startswith("//"),
            )
            cur.execute(
                fetch_query_string("delete_puzzle_file_for_puzzle.sql"),
                {"puzzle": puzzleData["id"]},
            )
            cur.execute(
                fetch_query_string("delete_piece_for_puzzle.sql"),
                {"puzzle": puzzleData["id"]},
            )

            msg = delete_puzzle_timeline(puzzle_id)
            if msg.get("status_code") >= 400:
                current_app.logger.error(msg.get("msg"))
                current_app.logger.error(
                    f"Failed delete of puzzle timeline for puzzle_id {puzzle_id}"
                )

            cur.execute(
                fetch_query_string("update_puzzle_status_for_puzzle.sql"),
                {"status": DELETED_REQUEST, "puzzle": puzzleData["id"]},
            )
            cur.execute(
                fetch_query_string("empty-user-puzzle-slot.sql"),
                {"player": user, "puzzle": puzzleData["id"]},
            )

            db.commit()
            sse.publish(
                "status:{}".format(DELETED_REQUEST),
                channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_id),
            )

            response = {
                "status": DELETED_REQUEST,
            }

        elif action == "freeze":
            cur.execute(
                fetch_query_string("update_puzzle_status_for_puzzle.sql"),
                {"status": FROZEN, "puzzle": puzzleData["id"]},
            )
            db.commit()
            sse.publish(
                "status:{}".format(FROZEN),
                channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_id),
            )

            response = {
                "status": FROZEN,
            }

        elif action == "unfreeze":
            # TODO: set status to COMPLETE if puzzle has been completed instead of ACTIVE
            cur.execute(
                fetch_query_string("update_puzzle_status_for_puzzle.sql"),
                {"status": ACTIVE, "puzzle": puzzleData["id"]},
            )
            db.commit()

            sse.publish(
                "status:{}".format(ACTIVE),
                channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_id),
            )
            response = {
                "status": ACTIVE,
            }

        elif action == "reset":
            if not (
                puzzleData.get("permission") == PRIVATE
                and not puzzleData.get("is_original")
                and puzzleData.get("status")
                in (FROZEN, BUGGY_UNLISTED, ACTIVE, COMPLETED)
            ):

                response = {"msg": "Only unlisted puzzle instances can be reset"}
                cur.close()
                return make_response(json.jsonify(response), 400)

            if puzzleData.get("status") not in (
                ACTIVE,
                COMPLETED,
                FROZEN,
                BUGGY_UNLISTED,
            ):
                response = {
                    "msg": "Puzzle is not in acceptable state in order to be reset"
                }
                cur.close()
                return make_response(json.jsonify(response), 400)

            if puzzleData.get("status") != ACTIVE:
                # Only update the response status if puzzle status is changing.
                # This way any response will trigger the "Reload" button since
                # the active puzzle status will have an empty response status.
                response = {"status": ACTIVE}

            job = current_app.cleanupqueue.enqueue(
                "api.jobs.piece_reset.reset_puzzle_pieces_and_handle_errors",
                puzzleData.get("id"),
                result_ttl=0,
            )

        cur.close()

        purge_route_from_nginx_cache(
            "/chill/site/front/{puzzle_id}/".format(puzzle_id=puzzle_id),
            current_app.config.get("PURGEURLLIST"),
        )
        return make_response(json.jsonify(response), 202)

    def get(self, puzzle_id):
        """
        deletePenalty: number;
        canFreeze: boolean;
        canDelete: boolean;
        canReset: boolean;
        hasActions: boolean;
        deleteDisabledMessage: string; //Not enough dots to delete this puzzle
        isFrozen: boolean;
        status: number;
        """
        ip = request.headers.get("X-Real-IP")
        user = int(current_app.secure_cookie.get("user") or user_id_from_ip(ip))

        cur = db.cursor()

        # validate the puzzle_id
        result = cur.execute(
            fetch_query_string("select-puzzle-details-for-puzzle_id.sql"),
            {"puzzle_id": puzzle_id},
        ).fetchall()
        if not result:
            # 400 if puzzle does not exist
            err_msg = {
                "msg": "No puzzle found",
            }
            cur.close()
            return make_response(json.jsonify(err_msg), 400)
        (result, col_names) = rowify(result, cur.description)
        puzzleData = result[0]

        (delete_penalty, can_delete, delete_disabled_message) = self.get_delete_prereq(
            puzzleData
        )
        response = {
            "canDelete": can_delete,
            "canFreeze": puzzleData.get("status") in (FROZEN, BUGGY_UNLISTED, ACTIVE),
            "canReset": puzzleData.get("permission") == PRIVATE
            and not puzzleData.get("is_original")
            and puzzleData.get("status") in (FROZEN, BUGGY_UNLISTED, ACTIVE, COMPLETED),
            "hasActions": puzzleData.get("status")
            in (
                FROZEN,
                ACTIVE,
                COMPLETED,
                BUGGY_UNLISTED,
                RENDERING_FAILED,
                REBUILD,
                IN_RENDER_QUEUE,
                MAINTENANCE,
            ),
            "deleteDisabledMessage": delete_disabled_message,
            "deletePenalty": delete_penalty,
            "isFrozen": puzzleData.get("status") == FROZEN,
            "status": puzzleData.get("status", -99),
        }
        cur.close()
        return make_response(json.jsonify(response), 200)


class PuzzleOriginalDetailsView(MethodView):
    """"""

    decorators = [user_not_banned]

    def get_bump_prereq(self, cur, user, puzzleData):
        highest_bid = 0
        can_bump = False
        bump_disabled_message = ""
        if puzzleData["status"] == IN_QUEUE:
            if puzzleData["queue"] > QUEUE_WINNING_BID:
                highest_bid = self.get_bid_amount(cur, puzzleData)

                player_points_result = cur.execute(
                    fetch_query_string("select-minimum-points-for-user.sql"),
                    {"points": highest_bid, "user": user},
                ).fetchone()
                if player_points_result:
                    can_bump = True

                if not can_bump:
                    bump_disabled_message = "Not enough dots to bump this puzzle."
            else:
                bump_disabled_message = "This puzzle is next in line to be active."
        return (highest_bid, can_bump, bump_disabled_message)

    def get_bid_amount(self, cur, puzzleData):
        "compute the winning bid amount"
        bid_amount = 0
        low, high = next(
            filter(
                lambda x: x[0] <= puzzleData["pieces"] and x[1] > puzzleData["pieces"],
                current_app.config["SKILL_LEVEL_RANGES"],
            )
        )
        queue_count_result = cur.execute(
            fetch_query_string("get-queue-count-for-skill-level.sql"),
            {"low": low, "high": high},
        ).fetchone()
        if queue_count_result and len(queue_count_result):
            bid_amount = (queue_count_result[0] + 1) * current_app.config[
                "BID_COST_PER_PUZZLE"
            ]
            return bid_amount

    def patch(self, puzzle_id):
        ip = request.headers.get("X-Real-IP")
        user = int(current_app.secure_cookie.get("user") or user_id_from_ip(ip))

        # validate the args and headers
        args = {}
        xhr_data = request.get_json()
        if xhr_data:
            args.update(xhr_data)
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # Verify args
        action = args.get("action")
        if action not in ORIGINAL_ACTIONS:
            abort(400)

        cur = db.cursor()

        # validate the puzzle_id
        result = cur.execute(
            fetch_query_string("select-puzzle-details-for-puzzle_id.sql"),
            {"puzzle_id": puzzle_id},
        ).fetchall()
        if not result:
            # 400 if puzzle does not exist
            err_msg = {
                "msg": "No puzzle found",
            }
            cur.close()
            return make_response(json.jsonify(err_msg), 400)
        (result, col_names) = rowify(result, cur.description)
        puzzleData = result[0]

        if not puzzleData["is_original"]:
            cur.close()
            abort(400)

        response = {}
        if action == "bump":
            bid_amount = self.get_bid_amount(cur, puzzleData)
            low, high = next(
                filter(
                    lambda x: x[0] <= puzzleData["pieces"]
                    and x[1] > puzzleData["pieces"],
                    current_app.config["SKILL_LEVEL_RANGES"],
                )
            )

            # check if player has enough dots for bumping puzzle up in queue
            player_points_result = cur.execute(
                fetch_query_string("select-minimum-points-for-user.sql"),
                {"points": bid_amount, "user": user},
            ).fetchone()
            if not player_points_result:
                cur.close()
                return make_response(json.jsonify({}), 400)

            # bump any puzzle that is currently at QUEUE_WINNING_BID to be QUEUE_BUMPED_BID
            cur.execute(
                fetch_query_string("bump-puzzle-winning-bid-to-bumped-bid.sql"),
                {"low": low, "high": high},
            )

            # bump this puzzle to be the winning bid and decrease player dots
            cur.execute(
                fetch_query_string("bump-puzzle-queue-winning-bid-for-puzzle.sql"),
                {"puzzle": puzzleData["id"]},
            )
            cur.execute(
                fetch_query_string("decrease-user-points.sql"),
                {"points": bid_amount, "user": user},
            )
            db.commit()

        else:
            cur.close()
            return make_response(json.jsonify({}), 400)

        cur.close()

        purge_route_from_nginx_cache(
            "/chill/site/front/{puzzle_id}/".format(puzzle_id=puzzle_id),
            current_app.config.get("PURGEURLLIST"),
        )
        return make_response(json.jsonify(response), 202)

    def get(self, puzzle_id):
        """
        highestBid: number;
        canBump: boolean;
        hasActions: boolean;
        bumpDisabledMessage: string; //Not enough dots to delete this puzzle
        status: number;
        """
        ip = request.headers.get("X-Real-IP")
        user = int(current_app.secure_cookie.get("user") or user_id_from_ip(ip))

        cur = db.cursor()

        # validate the puzzle_id
        result = cur.execute(
            fetch_query_string("select-puzzle-details-for-puzzle_id.sql"),
            {"puzzle_id": puzzle_id},
        ).fetchall()
        if not result:
            # 400 if puzzle does not exist
            err_msg = {
                "msg": "No puzzle found",
            }
            cur.close()
            return make_response(json.jsonify(err_msg), 400)
        (result, col_names) = rowify(result, cur.description)
        puzzleData = result[0]

        (highest_bid, can_bump, bump_disabled_message) = self.get_bump_prereq(
            cur, user, puzzleData
        )
        response = {
            "canBump": can_bump,
            "hasActions": puzzleData.get("status") == IN_QUEUE,
            "bumpDisabledMessage": bump_disabled_message,
            "highestBid": highest_bid,
            "status": puzzleData.get("status", -99),
        }
        cur.close()
        return make_response(json.jsonify(response), 200)


class InternalPuzzleDetailsView(MethodView):
    """"""

    def get(self, puzzle_id):
        result = get_puzzle_details(puzzle_id)
        if result["status_code"] >= 400:
            return make_response(json.jsonify(result), result["status_code"])

        return make_response(json.jsonify(result["result"]), result["status_code"])

    def patch(self, puzzle_id):
        data = request.get_json(silent=True)
        response_msg = update_puzzle_details(puzzle_id, data)

        if (
            response_msg.get("rowcount")
            and response_msg.get("status_code") == 200
            and data.get("status")
        ):
            purge_route_from_nginx_cache(
                "/chill/site/front/{puzzle_id}/".format(puzzle_id=puzzle_id),
                current_app.config.get("PURGEURLLIST"),
            )
        return make_response(json.jsonify(response_msg), response_msg["status_code"])


class InternalPuzzleDetailsByIdView(MethodView):
    """"""

    def get(self, pz_id):
        result = get_puzzle_details_by_id(pz_id)
        if result["status_code"] >= 400:
            return make_response(json.jsonify(result), result["status_code"])

        return make_response(json.jsonify(result["result"]), result["status_code"])


def get_puzzle_details(puzzle_id):
    """"""
    cur = db.cursor()
    # validate the puzzle_id
    result = cur.execute(
        fetch_query_string("select-internal-puzzle-details-for-puzzle_id.sql"),
        {"puzzle_id": puzzle_id},
    ).fetchall()
    if not result:
        # 404 if puzzle does not exist
        err_msg = {"msg": "No puzzle found", "status_code": 404}
        cur.close()
        return err_msg
    (result, col_names) = rowify(result, cur.description)
    puzzle_details = result[0]
    cur.close()
    msg = {"result": puzzle_details, "msg": "Success", "status_code": 200}
    return msg


def get_puzzle_details_by_id(pz_id):
    """"""
    cur = db.cursor()
    # validate the puzzle_id
    result = cur.execute(
        fetch_query_string("select-internal-puzzle-details-for-id.sql"),
        {"pz_id": pz_id},
    ).fetchall()
    if not result:
        # 404 if puzzle does not exist
        err_msg = {"msg": "No puzzle found", "status_code": 404}
        cur.close()
        return err_msg
    (result, col_names) = rowify(result, cur.description)
    puzzle_details = result[0]
    cur.close()
    msg = {"result": puzzle_details, "msg": "Success", "status_code": 200}
    return msg


def update_puzzle_details(puzzle_id, data):
    """"""
    fields = {
        "pieces",
        "rows",
        "cols",
        "piece_width",
        "mask_width",
        "table_width",
        "table_height",
        "name",
        "link",
        "description",
        "bg_color",
        "m_date",
        "owner",
        "queue",
        "status",
        "permission",
    }

    cur = db.cursor()
    # validate the puzzle_id
    result = cur.execute(
        fetch_query_string("select-internal-puzzle-details-for-puzzle_id.sql"),
        {"puzzle_id": puzzle_id},
    ).fetchall()
    if not result:
        # 400 if puzzle does not exist
        err_msg = {"msg": "No puzzle found", "status_code": 400}
        cur.close()
        return err_msg

    (result, col_names) = rowify(result, cur.description)
    original_details = result[0]

    if not data:
        err_msg = {"msg": "No JSON data sent", "status_code": 400}
        cur.close()
        return err_msg

    # verify that data keys are correct
    if not fields.issuperset(data.keys()):
        err_msg = {"msg": "Extra fields in JSON data were sent", "status_code": 400}
        cur.close()
        return err_msg

    params = {}
    params.update(original_details, **data)
    # Can't modify the puzzle_id or id fields
    params.update({"puzzle_id": puzzle_id, "id": original_details["id"]})
    result = cur.execute(
        fetch_query_string("patch_puzzle_details.sql"),
        params,
    )
    cur.close()
    db.commit()

    # publish a MAINTENANCE puzzle status change so players that happen to be on
    # a puzzle will get an alert message. This will require players to reload
    # the puzzle.
    if result.rowcount and data.get("status"):
        sse.publish(
            "status:{}".format(MAINTENANCE),
            channel="puzzle:{puzzle_id}".format(puzzle_id=puzzle_id),
        )

    msg = {"rowcount": result.rowcount, "msg": "Updated", "status_code": 200}
    return msg
