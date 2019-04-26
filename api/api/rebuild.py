from __future__ import absolute_import
from __future__ import division
from past.utils import old_div
import os
from random import randint

from flask import current_app, redirect, request, make_response, abort, request
from flask.views import MethodView
import redis
from PIL import Image

from .app import db

from .database import rowify
from .constants import REBUILD, COMPLETED
from .timeline import archive_and_clear
from .user import user_id_from_ip, user_not_banned
from .jobs.convertPiecesToRedis import convert
from .tools import deletePieceDataFromRedis

redisConnection = redis.from_url('redis://localhost:6379/0/', decode_responses=True)

query_select_puzzle_for_puzzle_id_and_status = """
select * from Puzzle where puzzle_id = :puzzle_id and status = :status
and strftime('%s', m_date) <= strftime('%s', 'now', '-7 hours');
"""

query_update_status_puzzle_for_puzzle_id = """
update Puzzle set status = :status, m_date = '', pieces = :pieces where puzzle_id = :puzzle_id;
"""

query_select_top_left_piece = """
select * from Piece where puzzle = :puzzle and row = 0 and col = 0;
"""

query_user_points_prereq = """
select u.points from User as u
join Puzzle as pz on (u.points >= :pieces)
where u.id = :user and pz.id = :puzzle;
"""

query_update_user_points_for_resetting_puzzle = """
update User set points = points - :points where id = :user;
"""

# From pieceRenderer
MIN_PIECE_SIZE = 64

class PuzzlePiecesRebuildView(MethodView):
    """
    When a puzzle is complete allow rebuilding it.
    """
    decorators = [user_not_banned]

    def post(self):
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        puzzle_id = args.get('puzzle_id')
        if not puzzle_id:
            abort(400)

        # Check pieces arg
        try:
            pieces = int(args.get('pieces', current_app.config['MINIMUM_PIECE_COUNT']))
        except ValueError as err:
            abort(400)
        if pieces < current_app.config['MINIMUM_PIECE_COUNT']:
            abort(400)

        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP')))

        cur = db.cursor()
        result = cur.execute(query_select_puzzle_for_puzzle_id_and_status, {'puzzle_id': puzzle_id, 'status': COMPLETED}).fetchall()
        if not result:
            # Puzzle does not exist or is not completed status.
            # Reload the page as the status may have been changed.
            return redirect('/chill/site/puzzle/{puzzle_id}/'.format(puzzle_id=puzzle_id))

        (result, col_names) = rowify(result, cur.description)
        puzzleData = result[0]
        puzzle = puzzleData['id']

        userHasEnoughPoints = cur.execute(query_user_points_prereq, {'user': user, 'puzzle': puzzle, 'pieces': pieces}).fetchall()
        if not userHasEnoughPoints:
            abort(400)

        # Get the adjusted piece count depending on the size of the original and
        # the minimum piece size.
        # TODO: Store the width and height of the original in the Puzzle
        # database table.
        puzzle_dir = os.path.join(current_app.config['PUZZLE_RESOURCES'], puzzle_id)
        imagefile = os.path.join(puzzle_dir, 'original.jpg')
        im = Image.open(imagefile)
        (width, height) = im.size
        im.close()
        max_pieces_that_will_fit = int((old_div(width,MIN_PIECE_SIZE))*(old_div(height,MIN_PIECE_SIZE)))

        # The user points for rebuilding the puzzle is decreased by the piece
        # count for the puzzle. Use at least 200 points for smaller puzzles.
        point_cost = max(current_app.config['MINIMUM_PIECE_COUNT'], min(max_pieces_that_will_fit, pieces, current_app.config['MAX_POINT_COST_FOR_REBUILDING']))
        cur.execute(query_update_user_points_for_resetting_puzzle, {'user': user, 'points': point_cost})

        # Update puzzle status to be REBUILD and change the piece count
        cur.execute(query_update_status_puzzle_for_puzzle_id, {'puzzle_id': puzzle_id, 'status': REBUILD, 'pieces': pieces})
        puzzleData['status'] = REBUILD
        puzzleData['pieces'] = pieces

        db.commit()

        # Delete any piece data from redis since it is no longer needed.
        query_select_all_pieces_for_puzzle = """select * from Piece where (puzzle = :puzzle)"""
        (all_pieces, col_names) = rowify(cur.execute(query_select_all_pieces_for_puzzle, {'puzzle': puzzle}).fetchall(), cur.description)
        deletePieceDataFromRedis(redisConnection, puzzle, all_pieces)

        job = current_app.createqueue.enqueue_call(
            func='api.jobs.pieceRenderer.render', args=([puzzleData]), result_ttl=0,
            timeout='24h'
        )

        archive_and_clear(puzzle)

        cur.close()
        db.commit()

        return redirect('/chill/site/puzzle/{puzzle_id}/'.format(puzzle_id=puzzle_id))
