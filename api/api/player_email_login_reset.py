"Player Email Login Reset"

import uuid

from flask import current_app, redirect, request, make_response, abort, json
from flask.views import MethodView

from api.app import db
from api.database import rowify, fetch_query_string
from api.user import user_id_from_ip, user_not_banned
from api.constants import EMAIL_MAXLENGTH
from api.notify import send_message


class PlayerEmailLoginResetView(MethodView):
    """
    Only allow users that are not currently signed in to reset their login by email.
    """

    decorators = [user_not_banned]

    def post(self):
        """"""
        response = {"message": "", "name": "error"}

        user = current_app.secure_cookie.get("user")
        if user:
            response[
                "message"
            ] = "User currently logged in.  No need to reset the login by e-mail."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        user = user_id_from_ip(request.headers.get("X-Real-IP"))
        if user == None:
            response["message"] = "Shared user not currently logged in."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        email = args.get("email", "").strip().lower()
        if len(email) > EMAIL_MAXLENGTH:
            response["message"] = "E-mail is too long."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        cur = db.cursor()

        # Get user by their verified email address
        result = cur.execute(
            fetch_query_string("get-user-by-verified-email-address.sql"),
            {"email": email},
        ).fetchone()
        if not result or result[0] == 0:
            response["message"] = "Sorry, that e-mail address has not been verified."
            response["name"] = "error"
            cur.close()
            db.commit()
            return make_response(json.jsonify(response), 400)
        else:
            user = result[0]

        result = cur.execute(
            fetch_query_string("select-player-details-for-player-id.sql"),
            {"player_id": user},
        ).fetchall()
        if not result:
            # This shouldn't happen if user-has-player-account.sql
            response["message"] = "No player account."
            response["name"] = "error"
            cur.close()
            db.commit()
            return make_response(json.jsonify(response), 400)
        (result, col_names) = rowify(result, cur.description)
        existing_player_data = result[0]

        if existing_player_data["has_active_reset_login_token"]:
            response[
                "message"
            ] = "Please check your e-mail for a reset login link.  The reset login link that was sent earlier has not expired."
            response["name"] = "error"
            cur.close()
            db.commit()
            return make_response(json.jsonify(response), 400)

        # Send a link to reset the login (silent fail if not configured)
        token = uuid.uuid4().hex
        message = """
The link below is only valid for a short time.  Use it to reset your login link
for Puzzle Massive.

http://{DOMAIN_NAME}/chill/site/reset-login/{token}/

After visiting that web page and clicking the reset login button; a new login
link will be created. Any older ones will no longer be valid.

You can ignore this message if you didn't initiate the request.
        """.format(
            token=token, DOMAIN_NAME=current_app.config.get("DOMAIN_NAME")
        )
        current_app.logger.debug(message)
        email_sent = False
        if not current_app.config.get("DEBUG", True):
            try:
                send_message(
                    email, "Puzzle Massive - reset login", message, current_app.config
                )
                email_sent = True
            except Exception as err:
                current_app.logger.warning(
                    "Failed to send reset login message. email: {email}\n {message}\n error: {err}".format(
                        err=err, email=email, message=message
                    )
                )
                email_sent = False

        cur.execute(
            fetch_query_string("update-player-account-login-token.sql"),
            {
                "player_id": user,
                "reset_login_token": token,
                "expire_token_timeout": "+1 day",
            },
        )

        if current_app.config.get("DEBUG", True):
            response[
                "message"
            ] = "A reset login link has been sent to your e-mail. DEBUG is True, so did not really send the email. Check the logs for the login link."
            response["name"] = "success"
        elif not email_sent:
            response[
                "message"
            ] = "Failed to send reset login link to your e-mail.".format(email)
            response["name"] = "error"
        else:
            response[
                "message"
            ] = "A reset login link has been sent to your e-mail.".format(email)
            response["name"] = "success"

        db.commit()
        cur.close()
        return make_response(json.jsonify(response), 202)
