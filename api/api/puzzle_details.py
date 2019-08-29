from flask import current_app, request, abort, json, make_response
from flask.views import MethodView
import redis

from api.app import db
from api.user import user_id_from_ip, user_not_banned
from api.database import fetch_query_string, rowify, delete_puzzle_resources
from api.constants import DELETED_REQUEST, FROZEN, ACTIVE, COMPLETED

redisConnection = redis.from_url('redis://localhost:6379/0/', decode_responses=True)

encoder = json.JSONEncoder(indent=2, sort_keys=True)

ACTIONS = (
    'delete',
    'freeze',
    'unfreeze'
    )

class PuzzleDetailsView(MethodView):
    """
    """

    decorators = [user_not_banned]

    def get_delete_prereq(self, puzzleData):
        delete_penalty = 0
        can_delete = True
        delete_disabled_message = ''
        if puzzleData['status'] != COMPLETED:
            delete_penalty = max(current_app.config['MINIMUM_PIECE_COUNT'], puzzleData['pieces'])
            can_delete = puzzleData['user_points'] >= delete_penalty
            if not can_delete:
                delete_disabled_message = 'Not enough dots to delete this puzzle'
        return (delete_penalty, can_delete, delete_disabled_message)

    def patch(self, puzzle_id):
        ip = request.headers.get('X-Real-IP')
        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(ip))

        # validate the args and headers
        args = {}
        xhr_data = request.get_json()
        if xhr_data:
            args.update(xhr_data)
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # Verify args
        action = args.get('action')
        if action not in ACTIONS:
            abort(400)

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

        if puzzleData['owner'] != user or puzzleData['is_original']:
            abort(400)

        response = {}

        if action == 'delete':

            (delete_penalty, can_delete, delete_disabled_message) = self.get_delete_prereq(puzzleData)
            if not can_delete:
                response = {
                    'msg': delete_disabled_message
                }
                return make_response(encoder.encode(response), 400)

            if delete_penalty > 0:
                cur.execute(fetch_query_string("decrease-user-points.sql"), {'user': user, 'points': delete_penalty})

            delete_puzzle_resources(puzzle_id)
            cur.execute(fetch_query_string("delete_puzzle_file_for_puzzle.sql"), {'puzzle': puzzleData['id']})
            cur.execute(fetch_query_string("delete_piece_for_puzzle.sql"), {'puzzle': puzzleData['id']})
            cur.execute(fetch_query_string('delete_puzzle_timeline.sql'), {'puzzle': puzzleData['id']})
            redisConnection.delete('timeline:{puzzle}'.format(puzzle=puzzleData['id']))
            redisConnection.delete('score:{puzzle}'.format(puzzle=puzzleData['id']))
            cur.execute(fetch_query_string("update_puzzle_status_for_puzzle.sql"), {'status': DELETED_REQUEST, 'puzzle': puzzleData['id']})
            cur.execute(fetch_query_string("empty-user-puzzle-slot.sql"), {'player': user, 'puzzle': puzzleData['id']})

            db.commit()

            response = {
                "status": DELETED_REQUEST,
            }

        elif action == 'freeze':
            cur.execute(fetch_query_string("update_puzzle_status_for_puzzle.sql"), {'status': FROZEN, 'puzzle': puzzleData['id']})
            db.commit()

            response = {
                "status": FROZEN,
            }

        elif action == 'unfreeze':
            # TODO: set status to COMPLETE if puzzle has been completed instead of ACTIVE
            cur.execute(fetch_query_string("update_puzzle_status_for_puzzle.sql"), {'status': ACTIVE, 'puzzle': puzzleData['id']})
            db.commit()

            response = {
                "status": ACTIVE,
            }

        cur.close()
        return make_response(encoder.encode(response), 202)

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

        (delete_penalty, can_delete, delete_disabled_message) = self.get_delete_prereq(puzzleData)
        response = {
            'canDelete': can_delete,
            'deleteDisabledMessage': delete_disabled_message,
            'deletePenalty': delete_penalty,
            'isFrozen': puzzleData.get('status') == FROZEN,
            'status': puzzleData.get('status', -99)
        }
        cur.close()
        return encoder.encode(response)
