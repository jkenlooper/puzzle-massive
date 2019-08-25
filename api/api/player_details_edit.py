"Admin Player Edit"

from flask import current_app, redirect, request, make_response, abort
from flask.views import MethodView

from api.app import db
from api.database import rowify, fetch_query_string, delete_puzzle_resources

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
