from __future__ import division
from builtins import str, bytes
from past.utils import old_div
import crypt
import string
import random
import time
import datetime
import hashlib

from flask import current_app, json, redirect, make_response, request, url_for
from flask.views import MethodView

from api.app import db, redis_connection
from api.database import rowify, fetch_query_string

LETTERS = "%s%s" % (string.ascii_letters, string.digits)

ADMIN_USER_ID = 1
ANONYMOUS_USER_ID = 2

LITTLE_LESS_THAN_A_WEEK = (60 * 60 * 24 * 7) - random.randint(3023, 3600 * 14)
LITTLE_MORE_THAN_A_DAY = (60 * 60 * 24) + random.randint(3023, 3600 * 14)
MAX_BAN_TIME = LITTLE_LESS_THAN_A_WEEK
HONEY_POT_BAN_TIME = LITTLE_MORE_THAN_A_DAY


def hidden_preview(puzzle_data):
    if puzzle_data.get("has_hidden_preview"):
        puzzle_data["src"] = ""
    return puzzle_data


def generate_password():
    "Create a random string for use as password. Return as cleartext and encrypted."
    timestamp = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
    random_int = random.randint(1, 99999)
    p_string = hashlib.sha224(
        bytes("%s%i" % (timestamp, int(old_div(random_int, 2))), "utf-8")
    ).hexdigest()[:13]
    salt = "%s%s" % (random.choice(LETTERS), random.choice(LETTERS))
    password = crypt.crypt(p_string, salt)

    return (p_string, password)


def generate_user_login():
    "Create a unique login"
    timestamp = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
    random_int = random.randint(1, 99999)
    login = hashlib.sha224(
        bytes("%s%i" % (timestamp, random_int), "utf-8")
    ).hexdigest()[:13]

    return login


def user_id_from_ip(ip, skip_generate=True):
    current_app.logger.debug(f"user_id_from_ip {ip}")
    # start = time.perf_counter()
    cur = db.cursor()

    shareduser = current_app.secure_cookie.get("shareduser")
    if shareduser != None:
        # Check if this shareduser is still valid and another user hasn't chosen
        # a bit icon.
        result = cur.execute(
            fetch_query_string("select-user-by-id-and-no-password.sql"),
            {"id": shareduser},
        ).fetchall()
        if result:
            cur.close()
            # end = time.perf_counter()
            # current_app.logger.debug("end 1 user_id_from_ip {}".format(end - start))
            return int(shareduser)

    # Handle players that had a cookie in their browser, but then deleted it.
    # Or new players that are from the same ip that existing players are on.
    # These players are shown the new-player page.
    result = cur.execute(
        fetch_query_string("select-user-id-by-ip-and-no-password.sql"), {"ip": ip}
    ).fetchall()
    user_id = ANONYMOUS_USER_ID

    # No ip in db so create it except if the skip_generate flag is set
    if not result:
        if skip_generate:
            cur.close()
            # end = time.perf_counter()
            # current_app.logger.debug("end 2 user_id_from_ip {}".format(end - start))
            return None
        login = generate_user_login()
        cur.execute(
            fetch_query_string("add-new-user-for-ip.sql"),
            {
                "ip": ip,
                "login": login,
                "points": current_app.config["NEW_USER_STARTING_POINTS"],
            },
        )
        db.commit()

        result = cur.execute(
            fetch_query_string("select-user-id-by-ip-and-login.sql"),
            {"ip": ip, "login": login},
        ).fetchall()
        (result, col_names) = rowify(result, cur.description)
        user_id = result[0]["id"]
    else:
        (result, col_names) = rowify(result, cur.description)
        user_id = result[0]["id"]

    cur.close()
    # end = time.perf_counter()
    # current_app.logger.debug("end 3 user_id_from_ip {}".format(end - start))
    return user_id


def user_not_banned(f):
    """Check if the user is not banned and respond with 429 if so"""

    def decorator(*args, **kwargs):
        ip = request.headers.get("X-Real-IP")
        user = current_app.secure_cookie.get("user") or user_id_from_ip(ip)
        current_app.logger.debug(f"user_not_banned")
        # start = time.perf_counter()
        if not user == None:
            user = int(user)
            banneduser_score = redis_connection.zscore("bannedusers", user)
            if banneduser_score:
                now = int(time.time())
                if banneduser_score > now:
                    # The user could be banned for many different reasons.  Most
                    # bans only last for a few seconds because of recent piece
                    # movements.
                    response = ". . . please wait . . ."
                    if "application/json" in request.headers.get("Accept"):
                        response = json.jsonify(
                            {
                                "msg": response,
                                "expires": banneduser_score,
                                "timeout": banneduser_score - now,
                                "type": "bannedusers",
                            }
                        )
                    # end = time.perf_counter()
                    # current_app.logger.debug(
                    #    "end 1 user_not_banned {}".format(end - start)
                    # )
                    return make_response(response, 429)

        # end = time.perf_counter()
        # current_app.logger.debug("end 2 user_not_banned {}".format(end - start))
        return f(*args, **kwargs)

    return decorator


def increase_ban_time(user, seconds):
    now = int(time.time())
    current = int(redis_connection.zscore("bannedusers", user) or now)
    current = max(current, now)
    ban_timestamp = min(current + seconds, now + MAX_BAN_TIME)
    redis_connection.zadd("bannedusers", {user: ban_timestamp})
    return {
        "msg": "Temporarily banned. Ban time has increased by {} seconds".format(
            seconds
        ),
        "type": "bannedusers",
        "user": user,
        "expires": ban_timestamp,
        "timeout": ban_timestamp - now,
    }


class CurrentUserIDView(MethodView):
    """
    Current user based on secure user cookie.
    """

    decorators = [user_not_banned]

    def get(self):
        """
        Return the user ID by secure cookie or by IP.  Sets the shareduser
        cookie if user is authenticated via their IP.
        """
        set_cookie = False
        user_has_password = False
        user = current_app.secure_cookie.get("user")

        if user is None:
            shareduser = current_app.secure_cookie.get("shareduser")
            if shareduser:
                shareduser = int(shareduser)
                cur = db.cursor()
                result = cur.execute(
                    fetch_query_string("select-user-by-id-and-has-password.sql"),
                    {"id": shareduser},
                ).fetchall()
                if result:
                    user_has_password = True
                cur.close()

            user = user_id_from_ip(
                request.headers.get("X-Real-IP"), skip_generate=False
            )
            if not current_app.secure_cookie.get("shareduser") or user_has_password:
                set_cookie = True
        user = int(user)

        response = make_response(str(user), 200)
        if set_cookie:
            current_app.secure_cookie.set(
                "shareduser", str(user), response, expires_days=365
            )
        return response


class GenerateAnonymousLogin(MethodView):
    """
    A new password is generated with the existin user login as an anonymous
    login link which the player will need to copy in order to login after the
    cookie expires.
    """

    decorators = [user_not_banned]

    def get(self):
        "Return an object to be used by the generateBitLink js call"

        user = current_app.secure_cookie.get("user")
        if user is None:
            return make_response("no user", 403)
        user = int(user)

        (p_string, password) = generate_password()

        # Store encrypted password in db
        cur = db.cursor()
        try:
            result = cur.execute(
                fetch_query_string("select-login-from-user.sql"), {"id": user}
            ).fetchall()
        except IndexError:
            # user may have been added after a db rollback
            cur.close()
            return make_response("no user", 404)

        if not result:
            cur.close()
            return make_response("no user", 404)

        (result, col_names) = rowify(result, cur.description)
        user_data = result[0]

        cur.execute(
            fetch_query_string("update-password-for-user.sql"),
            {"id": user, "password": password},
        )
        db.commit()

        cur.close()
        data = {"bit": "".join(["", "/puzzle-api/bit/", user_data["login"], p_string])}
        return make_response(json.jsonify(data), 200)


class GenerateAnonymousLoginByToken(MethodView):
    "Similar to GenerateAnonymousLogin except uses a valid reset_login_token"

    def post(self):
        "Return an object to be used by the generateBitLink js call"
        data = {"link": ""}

        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # check the token
        token = args.get("token", "").strip()
        if not token:
            data["message"] = "No token."
            data["name"] = "error"
            return make_response(json.jsonify(data), 400)

        (p_string, password) = generate_password()

        cur = db.cursor()

        # get user for that token
        result = cur.execute(
            fetch_query_string("select-user-by-reset-login-token.sql"), {"token": token}
        ).fetchall()
        (result, col_names) = rowify(result, cur.description)
        if not result or not result[0]:
            data["message"] = "This token is no longer valid"
            data["name"] = "error"
            cur.close()
            return make_response(json.jsonify(data), 400)

        user_data = result[0]
        user = int(user_data["user"])

        # Store encrypted password in db
        try:
            result = cur.execute(
                fetch_query_string("select-login-from-user.sql"), {"id": user}
            ).fetchall()
        except IndexError:
            # user may have been added after a db rollback
            data["message"] = "No user found."
            data["name"] = "error"
            cur.close()
            return make_response(json.jsonify(data), 400)

        if not result:
            data["message"] = "No user found."
            data["name"] = "error"
            cur.close()
            return make_response(json.jsonify(data), 400)

        (result, col_names) = rowify(result, cur.description)
        user_data = result[0]

        cur.execute(
            fetch_query_string("update-password-for-user.sql"),
            {"id": user, "password": password},
        )

        # null out the reset login token
        cur.execute(
            fetch_query_string("delete-player-reset-login-token.sql"), {"user": user}
        )

        db.commit()

        cur.close()

        data["link"] = "".join(["", "/puzzle-api/bit/", user_data["login"], p_string])
        data[
            "message"
        ] = "Login has been reset. Please follow the link shown and save it to login in again."
        data["name"] = "success"
        return make_response(json.jsonify(data), 200)


class UserLoginView(MethodView):
    """
    To maintain backwards compatibility this is rewritten in nginx from /puzzle-api/bit/<bitLink>
    """

    def get(self, anonymous_login):
        "Set the user cookie if correct anon bit link."
        login = anonymous_login[:13]
        password = anonymous_login[13:]
        cur = db.cursor()

        response = make_response(redirect("/"))

        result = cur.execute(
            fetch_query_string("select-user-by-login.sql"), {"login": login}
        ).fetchall()

        if not result:
            cur.close()
            return make_response("no user", 404)

        (result, col_names) = rowify(result, cur.description)
        user_data = result[0]

        expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
        if crypt.crypt(password, user_data["password"]) == user_data["password"]:
            current_app.secure_cookie.set("shareduser", "", response, expires=expires)
            current_app.secure_cookie.set(
                "user", str(user_data["id"]), response, expires_days=365
            )
            cur.execute(
                fetch_query_string("extend-cookie_expires-for-user.sql"),
                {"id": user_data["id"]},
            )
            db.commit()
        else:
            # Invalid anon login; delete cookie just in case it's there
            current_app.secure_cookie.set("user", "", response, expires=expires)

        cur.close()

        return response


class AdminUserLoginView(MethodView):
    """
    This endpoint should require authentication. See the location defined in the
    nginx config.
    Sets the user cookie to be '1' which is used for the admin player.
    Redirects to the admin page.
    """

    def get(self):
        cur = db.cursor()

        response = make_response(redirect("/chill/site/admin/puzzle/"))

        # Delete the shareduser cookie if it exists
        expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
        current_app.secure_cookie.set("shareduser", "", response, expires=expires)

        current_app.secure_cookie.set(
            "user", str(ADMIN_USER_ID), response, expires_days=365
        )
        cur.execute(
            fetch_query_string("extend-cookie_expires-for-user.sql"),
            {"id": ADMIN_USER_ID},
        )
        db.commit()

        cur.close()

        return response


class UserLogoutView(MethodView):
    """
    Deleting the user cookie will logout the user
    """

    decorators = [user_not_banned]

    def get(self):
        "Delete the cookie by setting the expires to the past."
        # TODO: needs to proxy pass redirect up or something?
        response = make_response(redirect("/"))
        expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
        current_app.secure_cookie.set("user", "", response, expires=expires)
        current_app.secure_cookie.set("shareduser", "", response, expires=expires)

        return response


class UserDetailsView(MethodView):
    """"""

    # after 14 days reset the expiration date of the cookie by setting will_expire_cookie
    # In select-user-details.sql the will_expire_cookie is set when it is within 7 days of expire date.
    # --strftime('%s', u.cookie_expires) <= strftime('%s', 'now', '+7 days') as will_expire_cookie,
    # The actual cookie expire date is set for 365 days and is extended every 7 days.

    decorators = [user_not_banned]

    def get(self):
        is_shareduser = False
        user = int(current_app.secure_cookie.get("user") or "0")
        if not user:
            user = int(user_id_from_ip(request.headers.get("X-Real-IP")))
            is_shareduser = True

        cur = db.cursor()

        try:
            result = cur.execute(
                fetch_query_string("select-user-details.sql"), {"id": user}
            ).fetchall()
        except IndexError:
            # user may have been added after a db rollback
            cur.close()
            return make_response("no user", 404)

        if not result:
            cur.close()
            return make_response("no user", 404)

        (result, col_names) = rowify(result, cur.description)
        user_details = result[0]
        user_details["isShareduser"] = is_shareduser
        user_details["score"] = user_details["score"] or 0
        user_details["dots"] = user_details["dots"] or 0

        extend_cookie = False
        if user_details["will_expire_cookie"] != 0:
            extend_cookie = True
            cur.execute(
                fetch_query_string("extend-cookie_expires-for-user.sql"),
                {"id": user_details["id"]},
            )
            db.commit()
        del user_details["will_expire_cookie"]

        user_has_name = bool(user_details["name"])
        if not user_has_name:
            user_details["name"] = ""
        if is_shareduser or not user_details["email"]:
            # email is not shown to shareduser accounts
            user_details["email"] = ""
        user_details["nameApproved"] = user_has_name and bool(
            user_details["name_approved"]
        )
        del user_details["name_approved"]
        user_details["nameRejected"] = (
            user_has_name and user_details["approved_date"] == None
        )
        user_details["emailVerified"] = bool(user_details["email_verified"])
        del user_details["email_verified"]

        puzzle_instance_list = []

        if user_details["puzzle_instance_count"] > 0:
            result = cur.execute(
                fetch_query_string("select-user-puzzle-slot-for-player.sql"),
                {"player": user},
            ).fetchall()
            if result:
                (result, col_names) = rowify(result, cur.description)

                def set_urls(puzzle_instance):
                    puzzle_id = puzzle_instance.get("puzzle_id")
                    front_url = None
                    if puzzle_id:
                        front_url = "/chill/site/front/{}/".format(puzzle_id)

                    return {
                        "front_url": front_url,
                        "src": puzzle_instance.get("src"),
                    }

                if isinstance(puzzle_instance_list, list):
                    puzzle_instance_list = list(
                        map(set_urls, map(hidden_preview, result))
                    )

        user_details["puzzle_instance_list"] = puzzle_instance_list

        # Check if shareduser can claim bit icon as user
        if current_app.secure_cookie.get("shareduser"):
            result = cur.execute(
                fetch_query_string("select-minimum-points-for-user.sql"),
                {
                    "user": user,
                    "points": current_app.config["MINIMUM_TO_CLAIM_ACCOUNT"],
                },
            ).fetchone()
            if result:
                user_details["can_claim_user"] = True

        cur.close()

        # extend the cookie
        response = make_response(json.jsonify(user_details), 200)
        if extend_cookie:
            # Only set user cookie if it exists
            if current_app.secure_cookie.get("user"):
                current_app.secure_cookie.set(
                    "user", str(user_details["id"]), response, expires_days=365
                )
            # Only set shareduser cookie if it exists
            if current_app.secure_cookie.get("shareduser"):
                current_app.secure_cookie.set(
                    "shareduser", str(user_details["id"]), response, expires_days=365
                )
        return response


class ClaimUserByTokenView(MethodView):
    """
    Claims the shareduser account to be a user account, but doesn't cost points.
    It is also used for verifying an email address for the user account.
    The claim-player-by-token page will show a button that sends a POST to this view.
    The page is accessed from a link in their e-mail.
    """

    decorators = [user_not_banned]

    def post(self):
        ""
        data = {}

        # Prevent creating a new user if no support for cookies. Player should
        # have 'ot' already set by viewing the page.
        uses_cookies = current_app.secure_cookie.get("ot")
        if not uses_cookies:
            data["message"] = "No cookies."
            data["name"] = "error"
            return make_response(json.jsonify(data), 400)

        # Verify user
        user = current_app.secure_cookie.get("user")
        is_shareduser = False
        if user == None:
            is_shareduser = True
            user = user_id_from_ip(request.headers.get("X-Real-IP"))
        if user == None:
            # remove cookies
            data["message"] = "Not logged in."
            data["name"] = "error"
            response = make_response(json.jsonify(data), 400)
            expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
            current_app.secure_cookie.set("user", "", response, expires=expires)
            current_app.secure_cookie.set("shareduser", "", response, expires=expires)
            return response
        user = int(user)

        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        token = args.get("token", "").strip()
        if not token:
            data["message"] = "No token."
            data["name"] = "error"
            return make_response(json.jsonify(data), 400)

        cur = db.cursor()

        result = cur.execute(
            fetch_query_string("user-has-player-account.sql"), {"player_id": user}
        ).fetchone()
        if not result or result[0] == 0:
            data[
                "message"
            ] = "No player account for this user.  Please use the same web browser that was used when submitting the e-mail address."
            data["name"] = "error"
            cur.close()
            return make_response(json.jsonify(data), 400)

        result = cur.execute(
            fetch_query_string("select-player-details-for-player-id.sql"),
            {"player_id": user},
        ).fetchall()
        if not result:
            data["message"] = "No player account."
            data["name"] = "error"
            cur.close()
            return make_response(json.jsonify(data), 400)
        (result, col_names) = rowify(result, cur.description)
        existing_player_data = result[0]

        if existing_player_data["email_verify_token"] != token:
            data["message"] = "Invalid token for this player."
            data["name"] = "error"
            cur.close()
            return make_response(json.jsonify(data), 400)

        if existing_player_data["is_verifying_email"] == 0:
            data["message"] = "Token for this player is no longer valid."
            data["name"] = "error"
            cur.close()
            return make_response(json.jsonify(data), 400)

        # Token is valid
        data["message"] = "Registered email"
        data["name"] = "success"
        response = make_response(json.jsonify(data), 202)

        # Update password when shareduser to convert to regular user.
        if is_shareduser:
            (p_string, password) = generate_password()
            cur.execute(
                fetch_query_string("update-user-from-shareduser.sql"),
                {
                    "id": user,
                    "password": password,
                    "ip": request.headers.get("X-Real-IP"),
                },
            )
            # Save as a cookie
            current_app.secure_cookie.set("user", str(user), response, expires_days=365)
            # Remove shareduser
            expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
            current_app.secure_cookie.set("shareduser", "", response, expires=expires)

        cur.execute(
            fetch_query_string("update-player-account-email-verified.sql"),
            {
                "player_id": user,
                "email_verified": 1,
            },
        )
        cur.execute(
            fetch_query_string("make-verified-email-unique.sql"),
            {
                "player_id": user,
                "email": existing_player_data["email"],
            },
        )

        cur.close()
        db.commit()
        return response


class InternalUserDetailsView(MethodView):
    """"""

    def get(self, user):
        cur = db.cursor()
        result = cur.execute(
            fetch_query_string("select-user-details-by-id.sql"),
            {
                "id": user,
            },
        ).fetchall()
        if not result:
            err_msg = {
                "msg": "No user found",
            }
            cur.close()
            return make_response(json.jsonify(err_msg), 404)
        (result, col_names) = rowify(result, cur.description)
        user_details = result[0]
        return make_response(json.jsonify(user_details), 200)


class AdminBannedUserList(MethodView):
    """
    user:
        timestamp:
    """

    def get(self):
        banned = {}

        bannedusers = redis_connection.zrevrangebyscore(
            "bannedusers", "+inf", int(time.time()), withscores=True
        )

        # Add user -> timestamp
        for (user, timestamp) in bannedusers:
            banned[user] = {"timestamp": timestamp}

        return json.jsonify(banned)

    def post(self):
        "Cleanup banned users"

        # clean up old banned users if any
        old_bannedusers_count = redis_connection.zremrangebyscore("bannedusers", 0, now)
        return old_bannedusers_count


class BanishSelf(MethodView):
    """
    Adds the ip and user id for the user calling it to the bannedusers list with
    the timestamp of when the ban will be lifted.
    """

    decorators = [user_not_banned]

    def process_any_key(self):
        ip = request.headers.get("X-Real-IP")
        user = int(
            current_app.secure_cookie.get("user")
            or user_id_from_ip(ip, skip_generate=False)
        )
        message = ""

        # Check if player has at least joined one piece before.
        cur = db.cursor()
        result = cur.execute(
            fetch_query_string("select-minimum-score-for-player.sql"),
            {"player": user, "score": 1},
        ).fetchall()
        if not result:
            message = "Press any key to continue . . ."
            increase_ban_time(user, HONEY_POT_BAN_TIME)
        else:
            message = "Any key is disabled.  Honey pot averted."

        cur.close()
        return make_response(message, 201)

    def get(self):
        "The url for this is listed in robots.txt under a Disallow"
        return self.process_any_key()

    def post(self):
        "User filled out and submitted the hidden form.  Most likely a spam bot."
        return self.process_any_key()
