from builtins import str
from random import randint
import datetime

from flask import current_app, abort, json, redirect, make_response, request
from flask.views import MethodView

from api.app import db
from api.database import rowify, fetch_query_string
from api.user import (
    generate_password,
    generate_user_login,
    user_id_from_ip,
    user_not_banned,
)
from api.tools import purge_route_from_nginx_cache

encoder = json.JSONEncoder(indent=2, sort_keys=True)


class ChooseBitView(MethodView):
    """Choose a bit"""

    decorators = [user_not_banned]

    def get(self):
        "Show a batch of available bit icon names"

        save_cookie = False
        offset_seconds = current_app.secure_cookie.get(u"ot")
        if not offset_seconds:
            save_cookie = True
            offset_seconds = str(randint(1, 900))
        offset_time = "{} seconds".format(int(offset_seconds))

        limit = request.args.get("limit")
        if not limit:
            limit = 7
        try:
            limit = int(limit)
        except ValueError:
            limit = 7
        if limit not in (48, 7):
            limit = 7

        cur = db.cursor()
        # List of bit icon names that are available
        result = cur.execute(
            fetch_query_string("select_random_bit_batch.sql"),
            {"offset_time": offset_time, "limit": limit},
        ).fetchall()
        (result, col_names) = rowify(result, cur.description)
        bits = [x["icon"] for x in result]

        response = make_response(encoder.encode({"data": bits}), 200)
        if save_cookie:
            current_app.secure_cookie.set(
                u"ot", str(offset_seconds), response, expires_days=1
            )

        cur.close()
        db.commit()
        return response


class ClaimBitView(MethodView):
    """Claim a bit and register new user"""

    decorators = [user_not_banned]

    def post(self):
        """If the bit icon is available; claim it for the user."""

        data = {"message": "", "name": "error"}

        icon = request.args.get("icon")
        if not icon:
            data["message"] = "No icon param passed"
            data["name"] = "error"
            return make_response(json.jsonify(data), 400)

        # Prevent creating a new user if no support for cookies. Player should
        # have 'ot' already set by viewing the page.
        uses_cookies = current_app.secure_cookie.get(u"ot")
        if not uses_cookies:
            data["message"] = "No ot cookie present"
            data["name"] = "error"
            return make_response(json.jsonify(data), 400)

        cur = db.cursor()

        # Check if bit icon is available
        result = cur.execute(
            fetch_query_string("select_available_bit_icon.sql"), {"icon": icon}
        ).fetchone()
        if not result:
            cur.close()
            db.commit()
            data["message"] = "That bit icon is no longer available."
            data["name"] = "error"
            return make_response(json.jsonify(data), 400)

        user = current_app.secure_cookie.get(u"user")
        if not user:
            user = user_id_from_ip(request.headers.get("X-Real-IP"))
            if user == None:
                data["message"] = "Not logged in."
                data["name"] = "error"
                cur.close()
                db.commit()
                return make_response(json.jsonify(data), 400)
            user = int(user)

        else:
            user = int(user)

        data["message"] = "Bit icon claimed by using {} of your dots.".format(
            current_app.config["POINT_COST_FOR_CHANGING_BIT"]
        )
        data["name"] = "success"
        response = make_response(json.jsonify(data), 200)

        # Unclaim any bit icon that the player already has
        cur.execute(fetch_query_string("unclaim_bit_icon.sql"), {"user": user})

        # Claim the bit icon
        cur.execute(
            fetch_query_string("update_bit_icon_user.sql"), {"user": user, "icon": icon}
        )
        cur.execute(
            fetch_query_string("decrease-user-points.sql"),
            {
                "points": current_app.config["POINT_COST_FOR_CHANGING_BIT"],
                "user": user,
            },
        )

        cur.close()
        db.commit()

        purge_route_from_nginx_cache(
            "/chill/site/internal/player-bit/{}/".format(user),
            current_app.config.get("PURGEURLLIST"),
        )

        return response


class ClaimUserView(MethodView):
    """Claim a bit and register new user"""

    decorators = [user_not_banned]

    def register_new_user(self, user_id):
        """Update initial ip tracked user to now be cookie tracked with a password."""
        cur = db.cursor()

        login = generate_user_login()
        (p_string, password) = generate_password()

        cur.execute(
            fetch_query_string("set-initial-password-for-user.sql"),
            {
                "id": user_id,
                "password": password,
                "ip": request.headers.get("X-Real-IP"),
            },
        )
        # Other players on the same network that are tracked by shareduser
        # cookie will have it updated to a new value.
        db.commit()
        cur.close()

    def post(self):
        """Update shareduser to user"""

        # Prevent creating a new user if no support for cookies. Player should
        # have 'ot' already set by viewing the page.
        uses_cookies = current_app.secure_cookie.get(u"ot")
        if not uses_cookies:
            abort(400)

        cur = db.cursor()

        response = make_response("", 200)

        user = user_id_from_ip(request.headers.get("X-Real-IP"))
        if user == None:
            abort(400)
        user = int(user)

        # Only set new user if enough dots
        result = cur.execute(
            fetch_query_string("select-minimum-points-for-user.sql"),
            {
                "user": user,
                "points": current_app.config["NEW_USER_STARTING_POINTS"]
                + current_app.config["POINT_COST_FOR_CHANGING_BIT"],
            },
        ).fetchone()
        if result:
            self.register_new_user(user)
            # Save as a cookie
            current_app.secure_cookie.set(
                u"user", str(user), response, expires_days=365
            )
            # Remove shareduser
            expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
            current_app.secure_cookie.set(u"shareduser", "", response, expires=expires)

            cur.execute(
                fetch_query_string("decrease-user-points.sql"),
                {
                    "user": user,
                    "points": current_app.config["POINT_COST_FOR_CHANGING_BIT"],
                },
            )

        cur.close()
        db.commit()
        return response
