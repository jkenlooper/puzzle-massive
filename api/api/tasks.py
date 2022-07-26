import sqlite3

from flask import current_app, make_response, request, abort, json
from flask.views import MethodView
import requests

from api.app import db
from api.database import rowify, fetch_query_string


def update_user_points_and_m_date(player, points, score):
    cur = db.cursor()
    try:
        result = cur.execute(
            fetch_query_string("update_user_points_and_m_date.sql"),
            {
                "id": player,
                "points": points,
                "score": score,
                "POINTS_CAP": current_app.config["POINTS_CAP"],
            },
        )
    except sqlite3.IntegrityError:
        err_msg = {
            "msg": "Database integrity error. Does the player ({}) exist?".format(
                player
            ),
            "status_code": 400,
        }
        cur.close()
        return err_msg
    cur.close()
    db.commit()
    msg = {"rowcount": result.rowcount, "msg": "Executed", "status_code": 200}
    return msg


def reward_player_for_score_threshold(player):
    cur = db.cursor()
    try:
        result = cur.execute(
            fetch_query_string(
                "reward_player_for_score_threshold--puzzle-instance-slot.sql"
            ),
            {
                "player": player,
                "score_threshold": int(
                    current_app.config.get("REWARD_INSTANCE_SLOT_SCORE_THRESHOLD", "0")
                ),
            },
        )

    except sqlite3.IntegrityError:
        err_msg = {
            "msg": "Database integrity error. Does the player ({}) exist?".format(
                player
            ),
            "status_code": 400,
        }
        cur.close()
        return err_msg
    cur.close()
    db.commit()
    msg = {"rowcount": result.rowcount, "msg": "Executed", "status_code": 200}
    return msg


def update_bit_icon_expiration(player):
    cur = db.cursor()
    try:
        result = cur.execute(
            fetch_query_string("update_bit_icon_expiration.sql"),
            {"user": player},
        )
    except sqlite3.IntegrityError:
        err_msg = {
            "msg": "Database integrity error. Does the player ({}) exist?".format(
                player
            ),
            "status_code": 400,
        }
        cur.close()
        return err_msg
    cur.close()
    db.commit()
    msg = {"rowcount": result.rowcount, "msg": "Executed", "status_code": 200}
    return msg


def update_points_to_minimum_for_all_users(minimum):
    cur = db.cursor()
    try:
        result = cur.execute(
            fetch_query_string("update_points_to_minimum_for_all_users.sql"),
            {"minimum": minimum},
        )
    except sqlite3.IntegrityError:
        err_msg = {
            "msg": "Database integrity error. update_points_to_minimum_for_all_users",
            "status_code": 400,
        }
        cur.close()
        return err_msg
    cur.close()
    db.commit()
    msg = {"rowcount": result.rowcount, "msg": "Executed", "status_code": 200}
    return msg


def update_user_name_approved_for_approved_date_due():
    cur = db.cursor()
    try:
        result = cur.execute(
            fetch_query_string("update-user-name-approved-for-approved_date-due.sql"),
        )
    except sqlite3.IntegrityError:
        err_msg = {
            "msg": "Database integrity error. update_user_name_approved_for_approved_date_due",
            "status_code": 400,
        }
        cur.close()
        return err_msg
    cur.close()
    db.commit()
    msg = {"rowcount": result.rowcount, "msg": "Executed", "status_code": 200}
    return msg


class InternalTasksStartView(MethodView):
    """
    Tasks are generally single database queries that need to have write access.
    """

    def post(self, task_name):
        "Start a task"

        # data is not a requirement since some tasks don't need extra params.
        data = request.get_json(silent=True) or {}

        if task_name == "update_user_points_and_m_date":
            if not data:
                response_msg = {"msg": "No JSON data sent", "status_code": 400}
            elif not {"player", "points", "score"} == data.keys():
                response_msg = {
                    "msg": "Extra fields in JSON data were sent",
                    "status_code": 400,
                }
            else:
                response_msg = update_user_points_and_m_date(**data)

        elif task_name == "update_bit_icon_expiration":
            if not data:
                response_msg = {"msg": "No JSON data sent", "status_code": 400}
            elif (
                not {
                    "player",
                }
                == data.keys()
            ):
                response_msg = {
                    "msg": "Extra fields in JSON data were sent",
                    "status_code": 400,
                }
            else:
                response_msg = update_bit_icon_expiration(**data)

        elif task_name == "update_points_to_minimum_for_all_users":
            if not data:
                response_msg = {"msg": "No JSON data sent", "status_code": 400}
            elif (
                not {
                    "minimum",
                }
                == data.keys()
            ):
                response_msg = {
                    "msg": "Extra fields in JSON data were sent",
                    "status_code": 400,
                }
            else:
                response_msg = update_points_to_minimum_for_all_users(**data)

        elif task_name == "update_user_name_approved_for_approved_date_due":
            if data:
                response_msg = {
                    "msg": "No JSON data should be sent",
                    "status_code": 400,
                }
            else:
                response_msg = update_user_name_approved_for_approved_date_due()

        elif task_name == "reward_player_for_score_threshold":
            if not data:
                response_msg = {"msg": "No JSON data sent", "status_code": 400}
            elif (
                not {
                    "player",
                }
                == data.keys()
            ):
                response_msg = {
                    "msg": "Extra fields in JSON data were sent",
                    "status_code": 400,
                }
            else:
                response_msg = reward_player_for_score_threshold(**data)

        else:
            response_msg = {
                "msg": "Task does not exist",
                "status_code": 404,
            }
        return make_response(json.jsonify(response_msg), response_msg["status_code"])
