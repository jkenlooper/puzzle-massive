#/newapi/create-puzzle-instance/
import os
import re
import time
import hashlib

from flask import current_app, redirect, make_response, abort, request
from flask.views import MethodView

from api.app import db
from api.database import rowify, fetch_query_string
from api.user import user_id_from_ip, user_not_banned
from api.constants import (
    PUBLIC,
    ACTIVE,
    IN_QUEUE,
    COMPLETED,
    FROZEN,
    REBUILD,
    IN_RENDER_QUEUE,
    RENDERING
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

        # Check bg_color
        color_regex = re.compile('.*?#?([a-f0-9]{6}|[a-f0-9]{3}).*?', re.IGNORECASE)
        bg_color = args.get('bg_color', '#808080')[:50]
        color_match = color_regex.match(bg_color)
        if (color_match):
            bg_color = "#{0}".format(color_match.group(1))
        else:
            bg_color = "#808080"

        # Check puzzle_id
        original_puzzle_id = args.get('puzzle_id')
        if (not original_puzzle_id):
            abort(400)

        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP')))

        cur = db.cursor()

        # The user should have
        # 2400 or more dots (points)
        # TODO: drop this dot requirement for creating puzzle instance
        userHasEnoughPoints = cur.execute(fetch_query_string("select-minimum-points-for-user.sql"), {'user': user, 'points': 2400}).fetchall()
        if not userHasEnoughPoints:
            abort(400)

        # An available instance slot (max count of 4)
        userHasAvailablePuzzleInstanceSlot = True # TODO: Create query to check if user has available slot
        if not userHasAvailablePuzzleInstanceSlot:
            abort(400)

        # TODO: Check if puzzle is valid to be a new puzzle instance
        cur = db.cursor()
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

        # TODO: copied from upload.py
        puzzle_id = None
        query = """select max(id)*13 from Puzzle;"""
        max_id = cur.execute(query).fetchone()[0] or 1 # in case there are no puzzles found.

        query = """select max(queue)+1 from Puzzle where permission = 0;"""
        count = cur.execute(query).fetchone()[0]
        if (not count):
          count = 1

        d = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
        puzzle_id = "%i%s" % (max_id, hashlib.sha224(bytes("%s%s" % (originalPuzzleData['name'], d), 'utf-8')).hexdigest()[0:9])

        # Create puzzle dir
        puzzle_dir = os.path.join(current_app.config.get('PUZZLE_RESOURCES'), puzzle_id)
        os.mkdir(puzzle_dir)


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

        classic_variant = cur.execute("select id from PuzzleVariant where slug = 'classic';").fetchone()[0]
        insert_puzzle_instance = "insert into PuzzleInstance (original, instance, variant) values (:originalPuzzle, :instance, :variant);"
        cur.execute(insert_puzzle_instance, {"originalPuzzle": originalPuzzleData['id'], "instance": puzzle, "variant": classic_variant})

        db.commit()
        cur.close()

        job = current_app.createqueue.enqueue_call(
            func='api.jobs.pieceRenderer.render', args=([puzzleData]), result_ttl=0,
            timeout='24h'
        )

        return redirect('/chill/site/puzzle/{0}/'.format(puzzle_id), code=303)
