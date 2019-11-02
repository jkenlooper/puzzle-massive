"Admin Player Name Register"

from flask import current_app, redirect, request, make_response, abort
from flask.views import MethodView

from api.app import db
from api.database import rowify, fetch_query_string, delete_puzzle_resources

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
