"Admin Puzzle Edit"

from flask import current_app, redirect, request, make_response, abort
from flask.views import MethodView

from api.app import db
from api.database import rowify
from api.constants import (
        ACTIVE,
        IN_QUEUE,
        COMPLETED,
        FROZEN,
        NEEDS_MODERATION,
        FAILED_LICENSE,
        NO_ATTRIBUTION,
        IN_RENDER_QUEUE,
        RENDERING,
        DELETED_LICENSE,
        DELETED_INAPT,
        DELETED_OLD,
        DELETED_REQUEST
        )

ACTIONS = (
    'approve',
    'reject',
    'delete',
    'tag'
    )

class AdminPuzzleBatchEditView(MethodView):
    """
    Handle editing a batch of puzzles.
    """
    def post(self):
        "Route is protected by basic auth in nginx"
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # TODO: Check user to see if role matches?
        # user = current_app.secure_cookie.get(u'user')
        # if not user:
        #     abort(403)

        # Verify args
        action = args.get('action')
        if action not in ACTIONS:
            abort(400)

        reject = args.get('reject')
        if action == 'reject' and reject not in ('license', 'attribution'):
            abort(400)

        delete = args.get('delete')
        if action == 'delete' and delete not in ('license', 'inapt', 'old', 'request'):
            abort(400)

        # abort if tag value not set
        tag = args.get('tag')
        if action == 'tag' and not tag:
            abort(400)

        puzzle_ids = request.form.getlist('montage_puzzle_id')
        if len(puzzle_ids) == 0:
            abort(400)
        if not isinstance(puzzle_ids, list):
            puzzle_ids = [puzzle_ids]

        if action == 'approve':
            query_update_status_for_puzzle_id = """
            -- IN_RENDER_QUEUE
            update Puzzle set status = -5
            -- NEEDS_MODERATION
            where status = 0
            and puzzle_id = :puzzle_id;
            """ #.format(IN_RENDER_QUEUE=IN_RENDER_QUEUE, NEEDS_MODERATION=NEEDS_MODERATION)

        if action == 'reject':
            status = None
            if reject == 'license':
                status = FAILED_LICENSE
            elif reject == 'attribution':
                status = NO_ATTRIBUTION
            # Careful not to allow for sql injection attack here.
            query_update_status_for_puzzle_id = """
            update Puzzle set status = {status}
            where status = {NEEDS_MODERATION}
            and puzzle_id = :puzzle_id;
            """.format(status=status, NEEDS_MODERATION=NEEDS_MODERATION)

        if action == 'delete':
            status = None
            if delete == 'license':
                status = DELETED_LICENSE
            elif delete == 'inapt':
                status = DELETED_INAPT
            elif delete == 'old':
                status = DELETED_OLD
            elif delete == 'request':
                status = DELETED_REQUEST
            # Careful not to allow for sql injection attack here.
            query_update_status_for_puzzle_id = """
            update Puzzle set status = {status}
            where puzzle_id = :puzzle_id;
            """.format(status=status)
            # TODO: delete puzzle resources

        cur = db.cursor()

        def each(puzzle_ids):
            for puzzle_id in puzzle_ids:
                print 'yield'
                print puzzle_id
                yield {'puzzle_id': puzzle_id}

        print query_update_status_for_puzzle_id
        print puzzle_ids
        cur.executemany(query_update_status_for_puzzle_id, each(puzzle_ids))
        db.commit()

        return make_response('204', 204)
