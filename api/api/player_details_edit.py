"Admin Player Edit"

from flask import current_app, redirect, request, make_response, abort
from flask.views import MethodView
from werkzeug.utils import escape

from api.app import db
from api.database import rowify, fetch_query_string, delete_puzzle_resources
from api.constants import POINTS_CAP, USER_NAME_MAXLENGTH, EMAIL_MAXLENGTH

SLOT_ACTIONS = (
    'add',
    'delete'
    )

class AdminPlayerDetailsEditView(MethodView):
    """
    Handle editing player details.
    """

    def post(self):
        "Route is protected by basic auth in nginx"
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        player = args.get('player')
        if not player:
            abort(400)
        email_verified = args.get('email_verified', '0')
        if not email_verified in ('0', '1'):
            abort(400)
        name_approved = args.get('name_approved', '0')
        if not name_approved in ('0', '1'):
            abort(400)

        name = escape(args.get('name'))
        if len(name) > USER_NAME_MAXLENGTH:
            abort(400)

        email = escape(args.get('email'))
        if len(email) > EMAIL_MAXLENGTH:
            abort(400)

        cur = db.cursor()

        result = cur.execute(fetch_query_string('user-has-player-account.sql'), {'player_id': player}).fetchone()
        if not result or result[0] == 0:
            cur.execute(fetch_query_string('init-player-account-for-user.sql'), {
                'player_id': player
            })

        result = cur.execute(fetch_query_string('select-admin-player-details-for-player-id.sql'), {'player_id': player}).fetchall()
        if not result:
            cur.close()
            abort(400)
        (result, col_names) = rowify(result, cur.description)
        existingPlayerData = result[0]

        if email == '':
            cur.execute(fetch_query_string('remove-player-account-email.sql'), {
                'player_id': player
            })
        else:
            cur.execute(fetch_query_string('update-player-account-email.sql'), {
                'player_id': player,
                'email': email
            })

        cur.execute(fetch_query_string('update-player-account-email-verified.sql'), {
            'player_id': player,
            'email_verified': int(email_verified),
        })

        cur.execute(fetch_query_string('update-user-points.sql'), {
            'player_id': player,
            'points': int(args.get('dots', existingPlayerData['dots'])),
            'POINTS_CAP': POINTS_CAP
        })

        if name == '':
            cur.execute(fetch_query_string('remove-user-name.sql'), {
                'player_id': player,
            })
        else:
            cur.execute(fetch_query_string('update-user-name.sql'), {
                'player_id': player,
                'name': name,
            })
        cur.execute(fetch_query_string('update-user-name-approved.sql'), {
            'player_id': player,
            'name_approved': int(name_approved),
        })

        cur.close()
        db.commit()

        return redirect('/chill/site/admin/player/details/{player}/'.format(player=player))



class AdminPlayerDetailsSlotsView(MethodView):
    """
    Handle editing player puzzle instance slots.
    """
    def post(self):
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # Verify args
        action = args.get('action')
        if action not in SLOT_ACTIONS:
            abort(400)

        player = args.get('player')
        if not player:
            abort(400)

        cur = db.cursor()

        if action == 'add':
            cur.execute(fetch_query_string("add-new-user-puzzle-slot.sql"), {'player': player})
        elif action == 'delete':
            cur.execute(fetch_query_string("delete-user-puzzle-slot.sql"), {'player': player})

        cur.close()
        db.commit()

        return redirect('/chill/site/admin/player/details/{player}/'.format(player=player))
