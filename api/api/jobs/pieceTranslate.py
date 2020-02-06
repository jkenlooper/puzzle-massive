from __future__ import division
from builtins import map
from builtins import zip
from builtins import str
from past.utils import old_div
import os.path
import math
import time
import sys

from flask import current_app
from flask_sse import sse

from api.database import rowify, fetch_query_string
from api.tools import (
    formatPieceMovementString,
    loadConfig,
    init_karma_key,
    get_db,
    get_redis_connection,
)
from api.constants import COMPLETED, QUEUE_END_OF_LINE
from api.piece_mutate import PieceMutateProcess

KARMA_POINTS_EXPIRE = 3600  # hour in seconds
RECENT_POINTS_EXPIRE = 7200
PIECE_GROUP_MOVE_MAX_BEFORE_PENALTY = 5
MAX_RECENT_POINTS = 25
MAX_KARMA = 25
MIN_KARMA = int(old_div(MAX_KARMA, 2)) * -1  # -12

# POINTS_CAP = 15000


class PieceGroupConflictError(Exception):
    """
    When some piece data from redis has changed after the process to update
    piece groups has happened.
    """


def get_earned_points(pieces):
    earns = 7
    if pieces < 200:
        earns = 0
    elif pieces < 400:
        earns = 1
    elif pieces < 800:
        earns = 2
    elif pieces < 1000:
        earns = 3
    elif pieces < 2000:
        earns = 4
    elif pieces < 3000:
        earns = 5
    elif pieces < 6000:
        earns = 6
    return earns


def translate(ip, user, puzzleData, piece, x, y, r, karma_change, db_file=None):
    def publishMessage(msg, karma_change, points=0, complete=False):
        # print(topic)
        # print(msg)
        sse.publish(
            msg,
            type="move",
            channel="puzzle:{puzzle_id}".format(puzzle_id=puzzleData["puzzle_id"]),
        )

        now = int(time.time())

        redis_connection.zadd("pcupdates", {puzzle: now})

        # TODO:
        # return (topic, msg)

        # bump the m_date for this player on the puzzle and timeline
        redis_connection.zadd("timeline:{puzzle}".format(puzzle=puzzle), {user: now})
        redis_connection.zadd("timeline", {user: now})

        # Update player points
        if points != 0 and user != None:
            redis_connection.zincrby(
                "score:{puzzle}".format(puzzle=puzzle), amount=1, value=user
            )
            redis_connection.sadd("batchuser", user)
            redis_connection.sadd("batchpuzzle", puzzle)
            redis_connection.incr("batchscore:{user}".format(user=user), amount=1)
            redis_connection.incr(
                "batchpoints:{puzzle}:{user}".format(puzzle=puzzle, user=user),
                amount=points,
            )
            redis_connection.zincrby("rank", amount=1, value=user)
            points_key = "points:{user}".format(user=user)
            pieces = int(puzzleData["pieces"])
            earns = get_earned_points(pieces)

            karma = int(redis_connection.get(karma_key))
            ## Max out recent points
            # if earns != 0:
            #    recent_points = int(redis_connection.get(points_key) or 0)
            #    if karma + 1 + recent_points + earns < MAX_KARMA:
            #        redis_connection.incr(points_key, amount=earns)
            # Doing small puzzles doesn't increase recent points, just extends points expiration.
            redis_connection.expire(points_key, RECENT_POINTS_EXPIRE)

            karma_change += 1
            # Extend the karma points expiration since it has increased
            redis_connection.expire(karma_key, KARMA_POINTS_EXPIRE)
            # Max out karma
            if karma < MAX_KARMA:
                redis_connection.incr(karma_key)
            else:
                # Max out points
                if earns != 0:
                    recent_points = int(redis_connection.get(points_key) or 0)
                    if recent_points + earns <= MAX_RECENT_POINTS:
                        redis_connection.incr(points_key, amount=earns)

            redis_connection.incr("batchpoints:{user}".format(user=user), amount=earns)

        # TODO: Optimize by using redis for puzzle status
        if complete:
            cur = db.cursor()

            cur.execute(
                fetch_query_string("update_puzzle_status_for_puzzle.sql"),
                {"puzzle": puzzle, "status": COMPLETED},
            )
            cur.execute(
                fetch_query_string("update_puzzle_queue_for_puzzle.sql"),
                {"puzzle": puzzle, "queue": QUEUE_END_OF_LINE},
            )
            db.commit()
            sse.publish(
                "status:{}".format(COMPLETED),
                channel="puzzle:{puzzle_id}".format(puzzle_id=puzzleData["puzzle_id"]),
            )
            job = current_app.cleanupqueue.enqueue_call(
                func="api.jobs.convertPiecesToDB.transfer", args=(puzzle,), result_ttl=0
            )

            db.commit()
            cur.close()

        # return topic and msg mostly for testing
        return (msg, karma_change)

    def savePiecePosition(puzzle, piece, x, y):
        # Move the piece
        redis_connection.hmset(
            "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece), {"x": x, "y": y}
        )
        redis_connection.zadd("pcx:{puzzle}".format(puzzle=puzzle), {piece: x})
        redis_connection.zadd("pcy:{puzzle}".format(puzzle=puzzle), {piece: y})

    def updateGroupedPiecesPositions(
        puzzle,
        piece,
        pieceGroup,
        offsetX,
        offsetY,
        groupedPiecesXY=None,
        newGroup=None,
        status=None,
    ):
        "Update all other pieces x,y in group to the offset, if newGroup then assign them to the newGroup"
        # TODO: pass in the pcg:{puzzle}:{pieceGroup} members as list of dict with properties.
        if groupedPiecesXY == None:
            allOtherPiecesInPieceGroup = redis_connection.smembers(
                "pcg:{puzzle}:{pieceGroup}".format(puzzle=puzzle, pieceGroup=pieceGroup)
            )
            allOtherPiecesInPieceGroup.remove(str(piece))
            allOtherPiecesInPieceGroup = list(allOtherPiecesInPieceGroup)
            pipe = redis_connection.pipeline(transaction=True)
            grouped_piece_property_list_x_y = ["x", "y"]
            for groupedPiece in allOtherPiecesInPieceGroup:
                pipe.hmget(
                    "pc:{puzzle}:{groupedPiece}".format(
                        puzzle=puzzle, groupedPiece=groupedPiece
                    ),
                    grouped_piece_property_list_x_y,
                )
            pc_puzzle_grouped_pieces = list(
                map(
                    lambda x: dict(
                        list(zip(grouped_piece_property_list_x_y, map(int, x)))
                    ),
                    pipe.execute(),
                ),
            )
            groupedPiecesXY = dict(
                list(zip(allOtherPiecesInPieceGroup, pc_puzzle_grouped_pieces))
            )

        pipe = redis_connection.pipeline(transaction=True)
        lines = []
        for groupedPiece in groupedPiecesXY.keys():
            newX = groupedPiecesXY[groupedPiece]["x"] + offsetX
            newY = groupedPiecesXY[groupedPiece]["y"] + offsetY
            newPC = {"x": newX, "y": newY}
            if newGroup != None:
                # Remove from the old group and place in newGroup
                newPC["g"] = newGroup
                pipe.sadd(
                    "pcg:{puzzle}:{g}".format(puzzle=puzzle, g=newGroup), groupedPiece
                )
                pipe.srem(
                    "pcg:{puzzle}:{g}".format(puzzle=puzzle, g=pieceGroup), groupedPiece
                )
            if status == "1":
                newPC["s"] = "1"
                pipe.sadd("pcfixed:{puzzle}".format(puzzle=puzzle), groupedPiece)
                pipe.srem("pcstacked:{puzzle}".format(puzzle=puzzle), groupedPiece)
            pipe.hmset(
                "pc:{puzzle}:{groupedPiece}".format(
                    puzzle=puzzle, groupedPiece=groupedPiece
                ),
                newPC,
            )
            pipe.zadd("pcx:{puzzle}".format(puzzle=puzzle), {groupedPiece: newX})
            pipe.zadd("pcy:{puzzle}".format(puzzle=puzzle), {groupedPiece: newY})
            lines.append(
                formatPieceMovementString(
                    groupedPiece, x=newX, y=newY, g=newGroup, s=status
                )
            )
        if status == "1":
            pipe.sadd("pcfixed:{puzzle}".format(puzzle=puzzle), piece)
            pipe.srem("pcstacked:{puzzle}".format(puzzle=puzzle), piece)
            pipe.hset(
                "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece), "s", "1"
            )
        if newGroup != None:
            # For the piece that doesn't need x,y updated remove from the old group and place in newGroup
            pipe.sadd("pcg:{puzzle}:{g}".format(puzzle=puzzle, g=newGroup), piece)
            pipe.srem("pcg:{puzzle}:{g}".format(puzzle=puzzle, g=pieceGroup), piece)
            pipe.hset(
                "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece), "g", newGroup
            )
            lines.append(formatPieceMovementString(piece, g=newGroup))
        pipe.execute()
        return lines

    # print('translate piece {piece} for puzzle: {puzzle_id}'.format(piece=piece, puzzle_id=puzzleData['puzzle_id']))

    p = ""
    points = 0
    puzzle = puzzleData["puzzle"]

    karma_key = init_karma_key(redis_connection, puzzle, ip)
    karma = int(redis_connection.get(karma_key))

    # Restrict piece to within table boundaries
    if x < 0:
        x = 0
    if x > puzzleData["table_width"]:
        x = puzzleData["table_width"]
    if y < 0:
        y = 0
    if y > puzzleData["table_height"]:
        y = puzzleData["table_height"]

    pc_puzzle_piece_key = "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece)

    # Get the puzzle piece origin position
    (originX, originY) = list(
        map(int, redis_connection.hmget(pc_puzzle_piece_key, ["x", "y"]),)
    )
    piece_mutate_process = PieceMutateProcess(redis_connection, puzzle, piece, x, y, r)
    (msg, status) = piece_mutate_process.start()

    if status == "stacked":
        # Decrease karma since stacking
        if karma > MIN_KARMA:
            redis_connection.decr(karma_key)
        karma_change -= 1

        return publishMessage(msg, karma_change,)
    elif status == "moved":
        # TODO
        pass
    elif status == "joined":
        # TODO
        pass
    else:
        # failed?
        # TODO
        pass

    piecesInProximity = piece_mutate_process.pieces_in_proximity_to_target

    lines = []

    p = msg

    # Set Piece Properties
    # originX, and originY are needed before calling savePiecePosition
    savePiecePosition(puzzle, piece, x, y)

    # Reset Piece Status for stacked (It's assumed that the piece being moved can't be a immovable piece)
    redis_connection.srem("pcstacked:{puzzle}".format(puzzle=puzzle), piece)
    redis_connection.hdel("pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece), "s")

    # Get Piece Properties
    pieceProperties = redis_connection.hgetall(pc_puzzle_piece_key)
    # print(pieceProperties)
    p += formatPieceMovementString(piece, **pieceProperties)

    # Get Adjacent Piece Properties
    adjacentPiecesList = list(
        map(
            int,
            [
                x
                for x in list(pieceProperties.keys())
                if x not in ("x", "y", "r", "w", "h", "b", "rotate", "g", "s")
            ],
        )
    )
    # TODO: why transaction False?
    pipe = redis_connection.pipeline(transaction=False)
    for adjacentPiece in adjacentPiecesList:
        pipe.hgetall(
            "pc:{puzzle}:{adjacentPiece}".format(
                puzzle=puzzle, adjacentPiece=adjacentPiece
            )
        )
    adjacentPieceProperties = dict(list(zip(adjacentPiecesList, pipe.execute())))
    # print adjacentPieceProperties

    tolerance = int(old_div(100, 2))

    # Check if piece is close enough to any adjacent piece
    pieceGroup = pieceProperties.get("g", None)
    # print 'pieceGroup = {0} {1}'.format(pieceGroup, isinstance(pieceGroup, str))
    hasProcessedPieceGroupMovement = False
    for adjacentPiece in adjacentPiecesList:
        # Skip if adjacent piece in same group
        if pieceGroup:
            if redis_connection.sismember(
                "pcg:{puzzle}:{pieceGroup}".format(
                    puzzle=puzzle, pieceGroup=pieceGroup
                ),
                adjacentPiece,
            ):
                # print('Skipping since adjacent piece in same group')
                continue

        (offsetFromPieceX, offsetFromPieceY) = list(
            map(int, pieceProperties.get(str(adjacentPiece)).split(","))
        )
        targetX = offsetFromPieceX + int(pieceProperties["x"])
        targetY = offsetFromPieceY + int(pieceProperties["y"])
        adjacentPieceProps = adjacentPieceProperties.get(adjacentPiece)

        xlow = targetX - tolerance
        xhigh = targetX + tolerance
        # print('check proximity for x {x} > {xlow} and {x} < {xhigh}'.format(x=adjacentPieceProps['x'], xlow=xlow, xhigh=xhigh))

        # Skip If the adjacent piece is not within range of the targetX and targetY
        if not (
            (int(adjacentPieceProps["x"]) > (targetX - tolerance))
            and (int(adjacentPieceProps["x"]) < (targetX + tolerance))
        ):
            # print('{adjacentPiece} not within x range'.format(adjacentPiece=adjacentPiece))
            continue

        ylow = targetY - tolerance
        yhigh = targetY + tolerance
        # print('check proximity for y {y} > {ylow} and {y} < {yhigh}'.format(y=adjacentPieceProps['y'], ylow=ylow, yhigh=yhigh))
        if not (
            (int(adjacentPieceProps["y"]) > (targetY - tolerance))
            and (int(adjacentPieceProps["y"]) < (targetY + tolerance))
        ):
            # print('{adjacentPiece} not within y range'.format(adjacentPiece=adjacentPiece))
            continue

        # print('{adjacentPiece} within range {x}, {y}'.format(adjacentPiece=adjacentPiece, x=adjacentPieceProps['x'], y=adjacentPieceProps['y']))

        # The piece can be joined to the adjacent piece
        points = 4
        pieceProperties["x"] = int(adjacentPieceProps["x"]) - offsetFromPieceX
        pieceProperties["y"] = int(adjacentPieceProps["y"]) - offsetFromPieceY

        # Set immovable status if adjacent piece is immovable (Will save and update other grouped pieces later)
        if adjacentPieceProps.get("s") == "1":
            pieceProperties["s"] = "1"

        savePiecePosition(puzzle, piece, x=pieceProperties["x"], y=pieceProperties["y"])

        # Update Piece group
        countOfPiecesInPieceGroup = redis_connection.scard(
            "pcg:{puzzle}:{g}".format(puzzle=puzzle, g=pieceProperties.get("g", piece))
        )
        adjacentPieceGroup = adjacentPieceProps.get("g", adjacentPiece)
        if countOfPiecesInPieceGroup == 0:
            # Update Piece group to that of the adjacent piece since it may already be in a group
            # print('add {piece} to adjacent pieces group {g}'.format(piece=piece, g=adjacentPieceGroup))
            redis_connection.sadd(
                "pcg:{puzzle}:{g}".format(puzzle=puzzle, g=adjacentPieceGroup),
                piece,
                adjacentPiece,
            )
            redis_connection.hset(
                "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece),
                "g",
                adjacentPieceGroup,
            )
            redis_connection.hset(
                "pc:{puzzle}:{adjacentPiece}".format(
                    puzzle=puzzle, adjacentPiece=adjacentPiece
                ),
                "g",
                adjacentPieceGroup,
            )

            # Save the piece immovable status
            if pieceProperties.get("s") == "1":
                redis_connection.hset(
                    "pc:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece), "s", "1"
                )
                redis_connection.sadd("pcfixed:{puzzle}".format(puzzle=puzzle), piece)

            pieceProperties["g"] = adjacentPieceGroup
            p += "\n" + formatPieceMovementString(piece, **pieceProperties)
            p += "\n" + formatPieceMovementString(adjacentPiece, g=adjacentPieceGroup)

        else:
            # Decide which group should be merged into the other
            # print('decide group for {piece}'.format(piece=piece))
            countOfPiecesInAdjacentPieceGroup = redis_connection.scard(
                "pcg:{puzzle}:{g}".format(puzzle=puzzle, g=adjacentPieceGroup)
            )
            # print('adjacentPieceGroup count: {0}'.format(countOfPiecesInAdjacentPieceGroup))
            # print('pieceGroup count: {0}'.format(countOfPiecesInPieceGroup))
            if adjacentPieceProps.get("s") == "1":
                # The adjacent piece is immovable so update all pieces that are joining to also be immovable
                # print('updating pieces in group to be in adjacent piece group and setting them to be immovable')
                lines = updateGroupedPiecesPositions(
                    puzzle,
                    piece,
                    pieceGroup,
                    int(pieceProperties["x"]) - originX,
                    int(pieceProperties["y"]) - originY,
                    newGroup=adjacentPieceGroup,
                    status="1",
                )
                pieceProperties["g"] = adjacentPieceGroup
            elif countOfPiecesInPieceGroup <= countOfPiecesInAdjacentPieceGroup:
                # print('updating pieces in group to be in adjacent piece group')
                lines = updateGroupedPiecesPositions(
                    puzzle,
                    piece,
                    pieceGroup,
                    int(pieceProperties["x"]) - originX,
                    int(pieceProperties["y"]) - originY,
                    newGroup=adjacentPieceGroup,
                )
                pieceProperties["g"] = adjacentPieceGroup

            elif countOfPiecesInAdjacentPieceGroup == 0:
                # The adjacent piece is not in a group
                # print('adjacent piece not in group')
                lines = [
                    formatPieceMovementString(adjacentPiece, g=pieceProperties["g"])
                ]

                # Update positions except the piece since its group is not changing either
                lines.extend(
                    updateGroupedPiecesPositions(
                        puzzle,
                        piece,
                        pieceGroup,
                        int(pieceProperties["x"]) - originX,
                        int(pieceProperties["y"]) - originY,
                    )
                )

                pipe = redis_connection.pipeline(transaction=True)
                pipe.sadd(
                    "pcg:{puzzle}:{g}".format(puzzle=puzzle, g=pieceProperties["g"]),
                    adjacentPiece,
                )
                pipe.hset(
                    "pc:{puzzle}:{adjacentPiece}".format(
                        puzzle=puzzle, adjacentPiece=adjacentPiece
                    ),
                    "g",
                    pieceProperties["g"],
                )
                pipe.execute()
            else:
                # Adjacent group is smaller so update just the group in adjacent pieces
                # print('updating adjacent piece group to be in moved piece group')
                lines = []

                # Update the positions of the moved group first
                lines.extend(
                    updateGroupedPiecesPositions(
                        puzzle,
                        piece,
                        pieceGroup,
                        int(pieceProperties["x"]) - originX,
                        int(pieceProperties["y"]) - originY,
                    )
                )

                # Add the adjacent pieces to the group
                # TODO: unless the adjacent piece is immovable
                piecesInAdjacentPieceGroup = redis_connection.smembers(
                    "pcg:{puzzle}:{adjacentPieceGroup}".format(
                        puzzle=puzzle, adjacentPieceGroup=adjacentPieceGroup
                    )
                )
                pipe = redis_connection.pipeline(transaction=True)
                for groupedAdjacentPiece in piecesInAdjacentPieceGroup:
                    pipe.sadd(
                        "pcg:{puzzle}:{g}".format(
                            puzzle=puzzle, g=pieceProperties["g"]
                        ),
                        groupedAdjacentPiece,
                    )
                    pipe.srem(
                        "pcg:{puzzle}:{g}".format(puzzle=puzzle, g=adjacentPieceGroup),
                        groupedAdjacentPiece,
                    )
                    pipe.hset(
                        "pc:{puzzle}:{groupedAdjacentPiece}".format(
                            puzzle=puzzle, groupedAdjacentPiece=groupedAdjacentPiece
                        ),
                        "g",
                        pieceProperties["g"],
                    )
                    lines.append(
                        formatPieceMovementString(
                            groupedAdjacentPiece, g=pieceProperties["g"]
                        )
                    )
                pipe.execute()

            # print lines
            p += "\n" + "\n".join(lines)
            p += "\n" + formatPieceMovementString(piece, **pieceProperties)
            hasProcessedPieceGroupMovement = True

        # No need to check other adjacent pieces
        break

    # Update other piece positions that are in the group if they haven't already been moved from the group merge
    if pieceGroup != None and not hasProcessedPieceGroupMovement:
        # Decrement karma since moving a piece that is in a group
        pieceGroupCount = redis_connection.scard(
            "pcg:{puzzle}:{pieceGroup}".format(puzzle=puzzle, pieceGroup=pieceGroup)
        )
        if pieceGroupCount > PIECE_GROUP_MOVE_MAX_BEFORE_PENALTY:
            # print 'decr karma since moving piec in group'
            if karma > MIN_KARMA:
                redis_connection.decr(karma_key)
            karma_change -= 1

        lines = updateGroupedPiecesPositions(
            puzzle,
            piece,
            pieceGroup,
            int(pieceProperties["x"]) - originX,
            int(pieceProperties["y"]) - originY,
        )
        p += "\n" + "\n".join(lines)

    # Check if the puzzle is complete
    complete = False
    if pieceProperties.get("s") == "1":
        immovableGroupCount = redis_connection.scard(
            "pcfixed:{puzzle}".format(puzzle=puzzle)
        )
        if int(immovableGroupCount) == int(puzzleData.get("pieces")):
            # print("Puzzle is complete: {0} == {1}".format(immovableGroupCount, puzzleData.get('pieces')))
            complete = True

    return publishMessage(p, karma_change, points=points, complete=complete,)


if __name__ == "__main__":
    config_file = sys.argv[1]
    config = loadConfig(config_file)

    db = get_db(config)
    redis_connection = get_redis_connection(config)

else:
    from api.app import db, redis_connection
