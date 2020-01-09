from flask import current_app, request, abort, json, make_response
from flask.views import MethodView

from api.app import db, redis_connection
from api.user import user_id_from_ip, user_not_banned
from api.database import fetch_query_string, rowify, delete_puzzle_resources
from api.constants import (
    DELETED_REQUEST,
    FROZEN,
    ACTIVE,
    COMPLETED,
    IN_QUEUE,
    SKILL_LEVEL_RANGES,
    BID_COST_PER_PUZZLE,
    QUEUE_WINNING_BID,
)

encoder = json.JSONEncoder(indent=2, sort_keys=True)

ORIGINAL_ACTIONS = ("bump",)

INSTANCE_ACTIONS = ("delete", "freeze", "unfreeze")


class PuzzleInstanceDetailsView(MethodView):
    """
    """

    decorators = [user_not_banned]

    def get_delete_prereq(self, puzzleData):
        delete_penalty = 0
        can_delete = True
        delete_disabled_message = ""
        if puzzleData["status"] != COMPLETED:
            delete_penalty = max(
                current_app.config["MINIMUM_PIECE_COUNT"], puzzleData["pieces"]
            )
            can_delete = puzzleData["user_points"] >= delete_penalty
            if not can_delete:
                delete_disabled_message = "Not enough dots to delete this puzzle"
        return (delete_penalty, can_delete, delete_disabled_message)

    def patch(self, puzzle_id):
        ip = request.headers.get("X-Real-IP")
        user = int(current_app.secure_cookie.get(u"user") or user_id_from_ip(ip))

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
            return make_response(encoder.encode(err_msg), 400)
        (result, col_names) = rowify(result, cur.description)
        puzzleData = result[0]

        if puzzleData["owner"] != user or puzzleData["is_original"]:
            abort(400)

        if puzzleData["status"] not in (FROZEN, ACTIVE, COMPLETED):
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
                return make_response(encoder.encode(response), 400)

            if delete_penalty > 0:
                cur.execute(
                    fetch_query_string("decrease-user-points.sql"),
                    {"user": user, "points": delete_penalty},
                )

            delete_puzzle_resources(puzzle_id)
            cur.execute(
                fetch_query_string("delete_puzzle_file_for_puzzle.sql"),
                {"puzzle": puzzleData["id"]},
            )
            cur.execute(
                fetch_query_string("delete_piece_for_puzzle.sql"),
                {"puzzle": puzzleData["id"]},
            )
            cur.execute(
                fetch_query_string("delete_puzzle_timeline.sql"),
                {"puzzle": puzzleData["id"]},
            )
            redis_connection.delete("timeline:{puzzle}".format(puzzle=puzzleData["id"]))
            redis_connection.delete("score:{puzzle}".format(puzzle=puzzleData["id"]))
            cur.execute(
                fetch_query_string("update_puzzle_status_for_puzzle.sql"),
                {"status": DELETED_REQUEST, "puzzle": puzzleData["id"]},
            )
            cur.execute(
                fetch_query_string("empty-user-puzzle-slot.sql"),
                {"player": user, "puzzle": puzzleData["id"]},
            )

            db.commit()

            response = {
                "status": DELETED_REQUEST,
            }

        elif action == "freeze":
            cur.execute(
                fetch_query_string("update_puzzle_status_for_puzzle.sql"),
                {"status": FROZEN, "puzzle": puzzleData["id"]},
            )
            db.commit()

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

            response = {
                "status": ACTIVE,
            }

        cur.close()
        return make_response(encoder.encode(response), 202)

    def get(self, puzzle_id):
        """
  deletePenalty: number;
  canDelete: boolean;
  hasActions: boolean;
  deleteDisabledMessage: string; //Not enough dots to delete this puzzle
  isFrozen: boolean;
  status: number;
        """
        ip = request.headers.get("X-Real-IP")
        user = int(current_app.secure_cookie.get(u"user") or user_id_from_ip(ip))

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
            return make_response(encoder.encode(err_msg), 400)
        (result, col_names) = rowify(result, cur.description)
        puzzleData = result[0]

        (delete_penalty, can_delete, delete_disabled_message) = self.get_delete_prereq(
            puzzleData
        )
        response = {
            "canDelete": can_delete,
            "hasActions": puzzleData.get("status") in (FROZEN, ACTIVE, COMPLETED),
            "deleteDisabledMessage": delete_disabled_message,
            "deletePenalty": delete_penalty,
            "isFrozen": puzzleData.get("status") == FROZEN,
            "status": puzzleData.get("status", -99),
        }
        cur.close()
        return encoder.encode(response)


class PuzzleOriginalDetailsView(MethodView):
    """
    """

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
                SKILL_LEVEL_RANGES,
            )
        )
        queue_count_result = cur.execute(
            fetch_query_string("get-queue-count-for-skill-level.sql"),
            {"low": low, "high": high},
        ).fetchone()
        if queue_count_result and len(queue_count_result):
            bid_amount = (queue_count_result[0] + 1) * BID_COST_PER_PUZZLE
            return bid_amount

    def patch(self, puzzle_id):
        ip = request.headers.get("X-Real-IP")
        user = int(current_app.secure_cookie.get(u"user") or user_id_from_ip(ip))

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
            return make_response(encoder.encode(err_msg), 400)
        (result, col_names) = rowify(result, cur.description)
        puzzleData = result[0]

        if not puzzleData["is_original"]:
            abort(400)

        response = {}
        if action == "bump":
            bid_amount = self.get_bid_amount(cur, puzzleData)
            low, high = next(
                filter(
                    lambda x: x[0] <= puzzleData["pieces"]
                    and x[1] > puzzleData["pieces"],
                    SKILL_LEVEL_RANGES,
                )
            )

            # check if player has enough dots for bumping puzzle up in queue
            player_points_result = cur.execute(
                fetch_query_string("select-minimum-points-for-user.sql"),
                {"points": bid_amount, "user": user},
            ).fetchone()
            if not player_points_result:
                cur.close()
                return make_response(encoder.encode({}), 400)

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
            return make_response(encoder.encode({}), 400)

        cur.close()
        return make_response(encoder.encode(response), 202)

    def get(self, puzzle_id):
        """
  highestBid: number;
  canBump: boolean;
  hasActions: boolean;
  bumpDisabledMessage: string; //Not enough dots to delete this puzzle
  status: number;
        """
        ip = request.headers.get("X-Real-IP")
        user = int(current_app.secure_cookie.get(u"user") or user_id_from_ip(ip))

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
            return make_response(encoder.encode(err_msg), 400)
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
        return encoder.encode(response)
