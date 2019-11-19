"Player Email Login Reset"

from flask import current_app, redirect, request, make_response, abort, json
from flask.views import MethodView

from api.app import db
from api.database import rowify, fetch_query_string
from api.user import user_id_from_ip, user_not_banned
from api.constants import EMAIL_MAXLENGTH

class PlayerEmailLoginResetView(MethodView):
    """
    Only allow users that are not currently signed in to reset their login by email.
    """

    decorators = [user_not_banned]

    def post(self):
        ""
        response = {
            "message": "",
            "name": "error"
        }

        user = current_app.secure_cookie.get(u'user')
        if user:
            response["message"] = "User currently logged in.  No need to reset the login by e-mail."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        user = user_id_from_ip(request.headers.get('X-Real-IP'))

        if user == None:
            response["message"] = "Shared user not currently logged in."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        user = int(user)

        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        email = args.get('email', '').strip().lower()
        if len(email) > EMAIL_MAXLENGTH:
            response["message"] = "E-mail is too long."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        cur = db.cursor()

        has_valid_email = True
        result = cur.execute(fetch_query_string('user-has-player-account.sql'), {'player_id': user}).fetchone()
        if not result or result[0] == 0:
            has_valid_email = False

        result = cur.execute(fetch_query_string('select-player-details-for-player-id.sql'), {'player_id': user}).fetchall()
        if not result:
            # This shouldn't happen if user-has-player-account.sql
            cur.close()
            response["message"] = "No player account."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)
        (result, col_names) = rowify(result, cur.description)
        existing_player_data = result[0]

        if not existing_player_data["email"] or not existing_player_data["email_verified"] or existing_player_data["is_verifying_email"]:
            has_valid_email = False

        if not has_valid_email:
            cur.close()
            response["message"] = "Sorry, that e-mail address has not been verified."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        if existing_player_data["has_active_reset_login_token"]:
            cur.close()
            response["message"] = "Please check your e-mail for a reset login link.  The reset login link that was sent earlier has not expired."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        #TODO: Send a link to reset the login

