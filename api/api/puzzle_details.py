from flask import current_app, request, abort, json, make_response
from flask.views import MethodView

from api.app import db
from api.user import user_id_from_ip, user_not_banned
from api.database import fetch_query_string, rowify

encoder = json.JSONEncoder(indent=2, sort_keys=True)

class PuzzleDetailsView(MethodView):
    """
    """

    decorators = [user_not_banned]

    def get(self, puzzle_id):
        """
  deletePenalty: number;
  canDelete: boolean;
  deleteDisabledMessage: string; //Not enough dots to delete this puzzle
  isFrozen: boolean;
  status: number;
        """
        ip = request.headers.get('X-Real-IP')
        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(ip))

        cur = db.cursor()

        # validate the puzzle_id
        result = cur.execute(fetch_query_string('select-puzzle-details-for-puzzle_id.sql'), {
            'puzzle_id': puzzle_id
            }).fetchall()
        if not result:
            # 400 if puzzle does not exist
            err_msg = {
                'msg': "No puzzle found",
            }
            cur.close()
            return make_response(encoder.encode(err_msg), 400)
        (result, col_names) = rowify(result, cur.description)
        puzzleData = result[0]

        # TODO: set the return values for puzzle-details
        response = {
            'deletePenalty': 0,
            'canDelete': True,
            'deleteDisabledMessage': 'Not enough dots to delete this puzzle',
            'isFrozen': False,
            'status': puzzleData.get('status', -99)
        }
        cur.close()
        return encoder.encode(response)
