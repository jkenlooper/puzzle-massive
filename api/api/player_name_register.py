"Admin Player Name Register"

from flask import current_app, redirect, request, make_response, abort, json
from flask.views import MethodView

from api.app import db
from api.database import rowify, fetch_query_string, delete_puzzle_resources
from api.user import user_id_from_ip, user_not_banned
from api.constants import USER_NAME_MAXLENGTH
from api.tools import normalize_name_from_display_name

POINT_COST_FOR_CHANGING_NAME = 100

ACTIONS = (
    'reject',
)

class AdminPlayerNameRegisterView(MethodView):
    """
    Handle actions on a batch of submitted names on the NameRegister.
    """
    def post(self):
        "Route is protected by basic auth in nginx"
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # Verify args
        action = args.get('action')
        if action not in ACTIONS:
            abort(400)

        name_register_ids = request.form.getlist('name_register_id')
        if len(name_register_ids) == 0:
            abort(400)
        if not isinstance(name_register_ids, list):
            name_register_ids = [name_register_ids]

        cur = db.cursor()

        if action == 'reject':
            def each(name_register_ids):
                for id in name_register_ids:
                    yield {'id': id}

            cur.executemany(fetch_query_string("reject-name-on-name-register-for-id.sql"), each(name_register_ids))

        db.commit()
        cur.close()
        return redirect('/chill/site/admin/name-register-review/')

class PlayerNameRegisterView(MethodView):
    """
    Handle actions for the player and any name that they own on the name register.
    """
    decorators = [user_not_banned]

    def post(self):
        ""
        response = {
            "message": "",
            "name": "error"
        }

        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP')))
        if user == None:
            response["message"] = "User not signed in."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)
        user = int(user)

        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        display_name = args.get('name', '').strip()
        name = normalize_name_from_display_name(display_name)

        # name is always converted to lowercase and display_name preserves
        # original case.
        display_name = args.get('name', '').strip()
        name = normalize_name_from_display_name(display_name)
        if len(display_name) > USER_NAME_MAXLENGTH:
            response["message"] = "Submitted name is too long."
            response["name"] = "error"
            return make_response(json.jsonify(response), 400)

        cur = db.cursor()

        result = cur.execute(fetch_query_string("select-minimum-points-for-user.sql"), {'user': user, 'points': POINT_COST_FOR_CHANGING_NAME}).fetchone()
        if not result:
            response["message"] = "Not enough points to change name."
            response["name"] = "error"
            cur.close()
            return make_response(json.jsonify(response), 400)
        else:
            if name == '':
                cur.execute(fetch_query_string('remove-user-name-on-name-register-for-player.sql'), {
                    'player_id': user,
                })
                cur.execute(fetch_query_string("decrease-user-points.sql"), {
                    "points": POINT_COST_FOR_CHANGING_NAME,
                    "user": user,
                })
                response["message"] = "Removed name."
                response["name"] = "success"
            else:
                result = cur.execute(fetch_query_string("check-status-of-name-on-name-register.sql"), {'name': name}).fetchall()
                if result:
                    (result, col_names) = rowify(result, cur.description)
                    name_status = result[0]
                    if name_status['rejected'] == 1:
                        response["message"] = "Submitted name has been rejected before."
                        response["name"] = "rejected"
                    elif name_status['claimed'] == 0 or name_status['user'] == user:
                        # The name is available and can be claimed. If owned by the
                        # user the casing of the letters can be modified.
                        cur.execute(fetch_query_string('remove-user-name-on-name-register-for-player.sql'), {
                            'player_id': user,
                        })

                        # Also updates the display_name if casing has changed
                        cur.execute(fetch_query_string('claim-user-name-on-name-register-for-player.sql'), {
                            'player_id': user,
                            'name': name,
                            'display_name': display_name,
                            'time': '+1 hour',
                        })
                        cur.execute(fetch_query_string("decrease-user-points.sql"), {
                            "points": POINT_COST_FOR_CHANGING_NAME,
                            "user": user,
                        })
                        response["message"] = "Submitted name ({}) reclaimed.".format(display_name)
                        response["name"] = "success"
                    else:
                        response["message"] = "Submitted name ({}) is currently used by another player.  Please try a different name.".format(display_name)
                        response["name"] = "rejected"
                else:
                    # name is new
                    cur.execute(fetch_query_string('remove-user-name-on-name-register-for-player.sql'), {
                        'player_id': user,
                    })
                    cur.execute(fetch_query_string('add-user-name-on-name-register-for-player-to-be-reviewed.sql'), {
                        'player_id': user,
                        'name': name,
                        'display_name': display_name,
                        'time': '+1 hour',
                    })

                    cur.execute(fetch_query_string("decrease-user-points.sql"), {
                        "points": POINT_COST_FOR_CHANGING_NAME,
                        "user": user,
                    })
                    response["message"] = "Thank you for submitting a new name.  \"{}\" will be shown next to your bit icon.".format(display_name)
                    response["name"] = "success"

        db.commit()
        cur.close()
        return make_response(json.jsonify(response), 200)
