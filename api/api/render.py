from __future__ import print_function
from __future__ import absolute_import
from flask import current_app, request, make_response, abort
from flask.views import MethodView

from api.app import db
from .database import read_query_file, rowify
from api.constants import IN_RENDER_QUEUE, REBUILD


class RenderPuzzlesView(MethodView):
    """"""

    def get(self):
        "Route is protected by basic auth in nginx"
        # TODO: Check user to see if role matches?
        # user = current_app.secure_cookie.get(u'user')
        # if not user:
        #     abort(403)

        cur = db.cursor()
        puzzles = rowify(
            cur.execute(
                read_query_file("select-puzzles-in-render-queue.sql"),
                {"IN_RENDER_QUEUE": IN_RENDER_QUEUE, "REBUILD": REBUILD},
            ).fetchall(),
            cur.description,
        )[0]
        print("found {0} puzzles to render".format(len(puzzles)))

        # push each puzzle to artist job queue
        for puzzle in puzzles:
            job = current_app.createqueue.enqueue(
                "api.jobs.pieceRenderer.render",
                [puzzle],
                result_ttl=0,
                timeout="24h",
            )

        response = make_response(
            """
        Starting render job.
        <a href="{url}">{url}</a>
        """.format(
                url=request.url
            ),
            202,
        )
        cur.close()
        return response
