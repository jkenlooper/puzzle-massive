#/newapi/puzzle-instance/
import os

from flask import current_app, redirect, make_response, abort, request
from flask.views import MethodView

from api.app import db
from api.database import rowify, fetch_query_string, generate_new_puzzle_id
from api.user import user_id_from_ip, user_not_banned
from api.tools import check_bg_color
from api.constants import (
    PUBLIC,
    ACTIVE,
    IN_QUEUE,
    COMPLETED,
    FROZEN,
    REBUILD,
    IN_RENDER_QUEUE,
    RENDERING,
    CLASSIC
)


class CreatePuzzleInstanceView(MethodView):
    """
    Handle a form submission to create a new puzzle instance from an existing puzzle.
    The player needs to have a minimum of 2400 dots
    An available puzzle instance slot
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

        bg_color = check_bg_color(args.get('bg_color', '#808080')[:50])

        # Check puzzle_id
        original_puzzle_id = args.get('puzzle_id')
        if (not original_puzzle_id):
            abort(400)

        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP')))

        cur = db.cursor()

        # The user should have
        # 2400 or more dots (points)
        # TODO: this could be configurable per site or for other reasons.
        #userHasEnoughPoints = cur.execute(fetch_query_string("select-minimum-points-for-user.sql"), {'user': user, 'points': 2400}).fetchall()
        #if not userHasEnoughPoints:
        #    abort(400)

        # An available instance slot
        result = cur.execute(fetch_query_string("select-available-user-puzzle-slot-for-player.sql"), {'player': user}).fetchone()[0]
        userHasAvailablePuzzleInstanceSlot = bool(result)
        if not userHasAvailablePuzzleInstanceSlot:
            abort(400)

        # Check if puzzle is valid to be a new puzzle instance
        result = cur.execute(fetch_query_string("select-valid-puzzle-for-new-puzzle-instance.sql"), {
            'puzzle_id': original_puzzle_id,
            'ACTIVE': ACTIVE,
            'IN_QUEUE': IN_QUEUE,
            'COMPLETED': COMPLETED,
            'FROZEN': FROZEN,
            'REBUILD': REBUILD,
            'IN_RENDER_QUEUE': IN_RENDER_QUEUE,
            'RENDERING': RENDERING,
            'PUBLIC': PUBLIC}).fetchall()
        if not result:
            # Puzzle does not exist or is not a valid puzzle to create instance from.
            abort(400)

        (result, col_names) = rowify(result, cur.description)
        originalPuzzleData = result[0]

        puzzle_id = generate_new_puzzle_id(originalPuzzleData['name'])

        # Create puzzle dir
        puzzle_dir = os.path.join(current_app.config.get('PUZZLE_RESOURCES'), puzzle_id)
        os.mkdir(puzzle_dir)

        query = """select max(queue)+1 from Puzzle where permission = 0;"""
        count = cur.execute(query).fetchone()[0]
        if (not count):
          count = 1

        d = {'puzzle_id':puzzle_id,
            'pieces':pieces,
            'name':originalPuzzleData['name'],
            'link':originalPuzzleData['link'],
            'description':originalPuzzleData['description'],
            'bg_color':bg_color,
            'owner':user,
            'queue':count,
            'status': IN_RENDER_QUEUE,
            'permission':PUBLIC}
        cur.execute("""insert into Puzzle (
        puzzle_id,
        pieces,
        name,
        link,
        description,
        bg_color,
        owner,
        queue,
        status,
        permission) values
        (:puzzle_id,
        :pieces,
        :name,
        :link,
        :description,
        :bg_color,
        :owner,
        :queue,
        :status,
        :permission);
        """, d)
        db.commit()

        result = cur.execute("select * from Puzzle where puzzle_id = :puzzle_id;", {'puzzle_id': puzzle_id}).fetchall()
        if not result:
            abort(500)

        (result, col_names) = rowify(result, cur.description)
        puzzleData = result[0]
        puzzle = puzzleData['id']

        classic_variant = cur.execute(fetch_query_string("select-puzzle-variant-id-for-slug.sql"), {"slug": CLASSIC}).fetchone()[0]
        cur.execute(fetch_query_string("insert-puzzle-instance.sql"), {"original": originalPuzzleData['id'], "instance": puzzle, "variant": classic_variant})

        cur.execute(fetch_query_string("fill-user-puzzle-slot.sql"), {'player': user, 'puzzle': puzzle})

        db.commit()
        cur.close()

        job = current_app.createqueue.enqueue_call(
            func='api.jobs.pieceRenderer.render', args=([puzzleData]), result_ttl=0,
            timeout='24h'
        )


        return redirect('/chill/site/puzzle/{0}/'.format(puzzle_id), code=303)
