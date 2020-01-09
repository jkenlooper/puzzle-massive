from __future__ import print_function
from __future__ import absolute_import
from builtins import range
from random import randint

from flask import current_app, redirect, request, make_response, abort, request
from flask.views import MethodView
import redis

from .app import db
from .database import rowify
from .constants import ACTIVE, COMPLETED
from .timeline import archive_and_clear
from .user import user_id_from_ip, user_not_banned
from .jobs.convertPiecesToRedis import convert

redisConnection = redis.from_url("redis://localhost:6379/0/", decode_responses=True)

query_select_puzzle_for_puzzle_id_and_status = """
select * from Puzzle where puzzle_id = :puzzle_id and status = :status
and strftime('%s', m_date) <= strftime('%s', 'now', '-7 hours');
"""

query_update_status_puzzle_for_puzzle_id = """
update Puzzle set status = :status, m_date = '' where puzzle_id = :puzzle_id;
"""

query_select_top_left_piece = """
select * from Piece where puzzle = :puzzle and row = 0 and col = 0;
"""

query_user_points_prereq = """
select u.points from User as u
join Puzzle as pz on (u.points >= pz.pieces)
where u.id = :user and pz.id = :puzzle;
"""

query_update_user_points_for_resetting_puzzle = """
update User set points = points - :points where id = :user;
"""


class PuzzlePiecesResetView(MethodView):
    """
    When a puzzle is complete allow resetting it.
    """

    decorators = [user_not_banned]

    def post(self):
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        puzzle_id = args.get("puzzle_id")
        if not puzzle_id:
            abort(400)

        user = int(
            current_app.secure_cookie.get(u"user")
            or user_id_from_ip(request.headers.get("X-Real-IP"))
        )

        cur = db.cursor()
        result = cur.execute(
            query_select_puzzle_for_puzzle_id_and_status,
            {"puzzle_id": puzzle_id, "status": COMPLETED},
        ).fetchall()
        if not result:
            # Puzzle does not exist or is not completed status.
            # Reload the page as the status may have been changed.
            return redirect(
                "/chill/site/puzzle/{puzzle_id}/".format(puzzle_id=puzzle_id)
            )

        (result, col_names) = rowify(result, cur.description)
        puzzleData = result[0]
        puzzle = puzzleData["id"]

        userHasEnoughPoints = cur.execute(
            query_user_points_prereq, {"user": user, "puzzle": puzzle}
        ).fetchall()
        if not userHasEnoughPoints:
            abort(403)

        cur.execute(
            query_update_user_points_for_resetting_puzzle,
            {"user": user, "points": puzzleData["pieces"]},
        )

        # Load the piece data from sqlite on demand
        if not redisConnection.zscore("pcupdates", puzzle):
            # TODO: check redis memory usage and create cleanup job if it's past a threshold
            memory = redisConnection.info(section="memory")
            print("used_memory: {used_memory_human}".format(**memory))
            maxmemory = memory.get("maxmemory")
            # maxmemory = 1024 * 2000
            if maxmemory != 0:
                target_memory = maxmemory * 0.5
                if memory.get("used_memory") > target_memory:
                    # push to queue for further processing
                    job = current_app.cleanupqueue.enqueue_call(
                        func="api.jobs.convertPiecesToDB.transferOldest",
                        args=(target_memory,),
                        result_ttl=0,
                    )

            # For now just convert as it doesn't take long
            convert(puzzle)

        # TODO: archive the timeline
        # timeline ui should only show when the puzzle is in 'complete' status.
        archive_and_clear(puzzle, db, current_app.config.get("PUZZLE_ARCHIVE"))

        (x1, y1, x2, y2) = (0, 0, puzzleData["table_width"], puzzleData["table_height"])

        (result, col_names) = rowify(
            cur.execute(
                query_select_top_left_piece, {"puzzle": puzzleData["id"]}
            ).fetchall(),
            cur.description,
        )
        topLeftPiece = result[0]
        allPiecesExceptTopLeft = list(range(0, puzzleData["pieces"]))
        allPiecesExceptTopLeft.remove(topLeftPiece["id"])

        # Create a pipe for buffering commands and disable atomic transactions
        pipe = redisConnection.pipeline(transaction=False)

        # Reset the pcfixed
        pipe.delete("pcfixed:{puzzle}".format(puzzle=puzzle))
        pipe.sadd("pcfixed:{puzzle}".format(puzzle=puzzle), topLeftPiece["id"])

        # Drop piece stacked
        pipe.delete("pcstacked:{puzzle}".format(puzzle=puzzle))

        # Drop piece X and Y
        pipe.delete("pcx:{puzzle}".format(puzzle=puzzle))
        pipe.delete("pcy:{puzzle}".format(puzzle=puzzle))

        # Drop immovable piece group
        pipe.delete(
            "pcg:{puzzle}:{topLeft}".format(
                puzzle=puzzle, topLeft=topLeftPiece["parent"]
            )
        )

        # Remove all piece groups and status
        for piece in allPiecesExceptTopLeft:
            # the piece status is removed here
            pipe.hdel(
                "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece), "g", "s"
            )

            # Remove these empty piece groups for each piece
            pipe.delete("pcg:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece))

        # Add top left piece group back in
        pipe.sadd(
            "pcg:{puzzle}:{topLeft}".format(
                puzzle=puzzle, topLeft=topLeftPiece["parent"]
            ),
            topLeftPiece["id"],
        )
        pipe.zadd(
            "pcx:{puzzle}".format(puzzle=puzzle),
            {topLeftPiece["id"]: topLeftPiece["x"]},
        )
        pipe.zadd(
            "pcy:{puzzle}".format(puzzle=puzzle),
            {topLeftPiece["id"]: topLeftPiece["y"]},
        )

        # Randomize piece x, y
        for piece in allPiecesExceptTopLeft:
            x = randint(x1, x2)
            y = randint(y1, y2)
            pipe.hmset(
                "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece),
                {"x": x, "y": y,},
            )
            pipe.zadd("pcx:{puzzle}".format(puzzle=puzzle), {piece: x})
            pipe.zadd("pcy:{puzzle}".format(puzzle=puzzle), {piece: y})

        pipe.execute()
        cur.execute(
            query_update_status_puzzle_for_puzzle_id,
            {"puzzle_id": puzzle_id, "status": ACTIVE},
        )
        cur.close()
        db.commit()

        return redirect("/chill/site/puzzle/{puzzle_id}/".format(puzzle_id=puzzle_id))
