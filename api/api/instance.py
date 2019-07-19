#/newapi/create-puzzle-instance/

from flask import current_app, redirect, make_response, abort, request
from flask.views import MethodView

from api.app import db
from api.user import user_id_from_ip, user_not_banned

query_user_points_prereq = """
select points from User
where id = :user and points > :points;
"""

class CreatePuzzleInstanceView(MethodView):
    """
    """
    decorators = [user_not_banned]

    def post(self):
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # Check pieces arg
        try:
            pieces = int(args.get('pieces', current_app.config['MINIMUM_PIECE_COUNT']))
        except ValueError as err:
            abort(400)
        if pieces < current_app.config['MINIMUM_PIECE_COUNT']:
            abort(400)

        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP')))

        # The user should have
        # 2400 or more dots (points)
        # An available instance slot (max count of 4)
        #
        userHasEnoughPoints = cur.execute(query_user_points_prereq, {'user': user, 'puzzle': puzzle, 'pieces': pieces}).fetchall()
        if not userHasEnoughPoints:
            abort(400)

        userCanRebuildPuzzle = cur.execute(fetch_query_string("select-user-rebuild-puzzle-prereq.sql"), {'user': user, 'puzzle': puzzle, 'pieces': pieces}).fetchall()
        if not userCanRebuildPuzzle:
            abort(400)

        # Check if puzzle is valid
        cur = db.cursor()
        result = cur.execute(fetch_query_string(".sql"), {'puzzle_id': puzzle_id, 'status': COMPLETED}).fetchall()
        if not result:
            # Puzzle does not exist or is not a valid puzzle to create instance
            # from.
            # TODO: Redirect to ?
            return redirect('/chill/site/front/{puzzle_id}/'.format(puzzle_id=puzzle_id))
