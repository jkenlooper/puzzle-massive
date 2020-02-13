"Player Email Register"

import uuid

from flask import current_app, redirect, request, make_response, abort, json
from flask.views import MethodView

from api.app import db
from api.database import rowify, fetch_query_string
from api.user import user_id_from_ip, user_not_banned
from api.constants import EMAIL_MAXLENGTH
from api.notify import send_message


class PlayerEmailRegisterView(MethodView):
    """
    """

    decorators = [user_not_banned]

    def post(self):
        ""
        response = {"message": "", "name": "error"}

        is_shareduser = False
        user = current_app.secure_cookie.get(u"user")
        if not user:
            user = user_id_from_ip(request.headers.get("X-Real-IP"))
            is_shareduser = True

        if user == None:
            response["message"] = "User not signed in."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        user = int(user)

        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        email = args.get("email", "").strip().lower()
        if len(email) > EMAIL_MAXLENGTH:
            response["message"] = "E-mail is too long."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        cur = db.cursor()

        result = cur.execute(
            fetch_query_string("user-has-player-account.sql"), {"player_id": user}
        ).fetchone()
        if not result or result[0] == 0:
            cur.execute(
                fetch_query_string("init-player-account-for-user.sql"),
                {"player_id": user},
            )

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

        # Prevent shareduser changing the verified email address.
        if is_shareduser and existing_player_data["is_verifying_email"]:
            response[
                "message"
            ] = "A player on this same network has already submitted an email address. Changing it is not allowed until the account has been claimed or the verify email token expires."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        if existing_player_data["email"] == email:
            response[
                "message"
            ] = "No changes made to e-mail address ({}).  The e-mail address is stored as lowercase.".format(
                email
            )
            response["name"] = "error"
        else:
            if email == "":
                cur.execute(
                    fetch_query_string("remove-player-account-email.sql"),
                    {"player_id": user},
                )
                response["message"] = "Removed e-mail from player account."
                response["name"] = "success"
            else:
                # Verify that email is unique
                result = cur.execute(
                    fetch_query_string("select-player-by-verified-email-address.sql"),
                    {"email": email},
                ).fetchall()
                if result:
                    response[
                        "message"
                    ] = "A player has already registered this e-mail address."
                    response["name"] = "error"
                    cur.close()
                    db.commit()
                    return make_response(json.jsonify(response), 400)

                if existing_player_data["is_verifying_email"]:
                    response[
                        "message"
                    ] = "An e-mail address is already in the process of verification for this player.  Please wait."
                    response["name"] = "error"
                    cur.close()
                    db.commit()
                    return make_response(json.jsonify(response), 400)

                cur.execute(
                    fetch_query_string("update-player-account-email.sql"),
                    {"player_id": user, "email": email},
                )
                cur.execute(
                    fetch_query_string("update-player-account-email-verified.sql"),
                    {"player_id": user, "email_verified": 0,},
                )

                # Send verification email (silent fail if not configured)
                token = uuid.uuid4().hex
                message = """
Please verify your e-mail address with Puzzle Massive by following the link below.

http://{DOMAIN_NAME}/chill/site/claim-player/{token}/

Complete registering your e-mail address by visiting that web page and clicking
the "verify player" button.

You can ignore this message if you didn't initiate the request.
                """.format(
                    token=token, DOMAIN_NAME=current_app.config.get("DOMAIN_NAME")
                )
                current_app.logger.debug(message)
                if not current_app.config.get("DEBUG", True):
                    try:
                        send_message(
                            email,
                            "Puzzle Massive - verify e-mail address",
                            message,
                            current_app.config,
                        )
                    except Exception as err:
                        current_app.logger.warning(
                            "Failed to send verification message. email: {email}\n {message}\n error: {err}".format(
                                err=err, email=email, message=message
                            )
                        )
                        pass

                cur.execute(
                    fetch_query_string("update-player-account-email-verify-token.sql"),
                    {
                        "player_id": user,
                        "email_verify_token": token,
                        "expire_token_timeout": "+1 hour",
                    },
                )

                response[
                    "message"
                ] = "Updated e-mail ({}) for player account.  ".format(email)
                response["name"] = "success"

        db.commit()
        cur.close()
        return make_response(json.jsonify(response), 202)
