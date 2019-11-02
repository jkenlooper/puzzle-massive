"Admin Puzzle Edit"
import os

from flask import current_app, redirect, request, make_response, abort
from flask.views import MethodView
import redis

from api.app import db
from api.database import rowify, fetch_query_string, delete_puzzle_resources
from api.constants import (
        ACTIVE,
        IN_QUEUE,
        COMPLETED,
        FROZEN,
        NEEDS_MODERATION,
        FAILED_LICENSE,
        NO_ATTRIBUTION,
        IN_RENDER_QUEUE,
        REBUILD,
        RENDERING,
        DELETED_LICENSE,
        DELETED_INAPT,
        DELETED_OLD,
        DELETED_REQUEST
        )

redisConnection = redis.from_url('redis://localhost:6379/0/', decode_responses=True)

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
        if len(puzzle_ids) == 0 or len(puzzle_ids) > 20:
            abort(400)
        if not isinstance(puzzle_ids, list):
            puzzle_ids = [puzzle_ids]

        cur = db.cursor()
        status = None

        if action == 'approve':
            status = IN_RENDER_QUEUE

        if action == 'reject':
            if reject == 'license':
                status = FAILED_LICENSE
            elif reject == 'attribution':
                status = NO_ATTRIBUTION

        if action == 'delete':
            if delete == 'license':
                status = DELETED_LICENSE
            elif delete == 'inapt':
                status = DELETED_INAPT
            elif delete == 'old':
                status = DELETED_OLD
            elif delete == 'request':
                status = DELETED_REQUEST

            for puzzle_id in puzzle_ids:
                delete_puzzle_resources(puzzle_id)
                id = cur.execute(fetch_query_string("select_puzzle_id_by_puzzle_id.sql"), {'puzzle_id': puzzle_id}).fetchone()[0]
                #current_app.logger.info('deleting puzzle resources for id {}'.format(id))
                cur.execute(fetch_query_string("delete_puzzle_file_for_puzzle.sql"), {'puzzle': id})
                cur.execute(fetch_query_string("delete_piece_for_puzzle.sql"), {'puzzle': id})
                cur.execute(fetch_query_string('delete_puzzle_timeline.sql'), {'puzzle': id})
                redisConnection.delete('timeline:{puzzle}'.format(puzzle=id))
                redisConnection.delete('score:{puzzle}'.format(puzzle=id))
            db.commit()


        def each(puzzle_ids):
            for puzzle_id in puzzle_ids:
                yield {'puzzle_id': puzzle_id, 'status': status}

        cur.executemany(fetch_query_string("update_puzzle_status_for_puzzle_id.sql"), each(puzzle_ids))
        db.commit()

        if action == 'approve':
            puzzles = rowify(cur.execute(fetch_query_string("select-puzzles-in-render-queue.sql"),
                {'IN_RENDER_QUEUE': IN_RENDER_QUEUE,
                 'REBUILD': REBUILD})
                .fetchall(), cur.description)[0]
            print("found {0} puzzles to render".format(len(puzzles)))

            # push each puzzle to artist job queue
            for puzzle in puzzles:
                job = current_app.createqueue.enqueue_call(
                    func='api.jobs.pieceRenderer.render', args=([puzzle]), result_ttl=0,
                    timeout='24h'
                )

        # TODO: if action in ('reject', 'delete'): #Also apply to any puzzle instances

        cur.close()
        return make_response('204', 204)
