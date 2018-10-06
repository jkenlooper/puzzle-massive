import time

from flask import current_app, make_response, request, abort, json

from flask.views import MethodView
from werkzeug.exceptions import HTTPException
import redis

from app import db
from database import fetch_query_string, rowify
from tools import formatPieceMovementString
from jobs.convertPiecesToRedis import convert

from constants import ACTIVE, IN_QUEUE
#from jobs import pieceMove

encoder = json.JSONEncoder(indent=2, sort_keys=True)

redisConnection = redis.from_url('redis://localhost:6379/0/')

# TODO: create a puzzle status web socket that will update when the status of
# the puzzle changes from converting, done, active, etc.

class PuzzlePiecesView(MethodView):
    """
    Gets piece data for a puzzle
    """

    def get(self, puzzle_id):
        ""

        cur = db.cursor()
        result = cur.execute(fetch_query_string('select_puzzle_id_by_puzzle_id.sql'), {
            'puzzle_id': puzzle_id
            }).fetchall()
        if not result:
            # 404 if puzzle or piece does not exist
            abort(404)

        (result, col_names) = rowify(result, cur.description)
        puzzle = result[0].get('puzzle')

        #TODO: if puzzle is not in redis then create a job to convert and respond with a 202 Accepted
        # if job is already active for this request respond with 202 Accepted

        # Load the piece data from sqlite on demand
        if not redisConnection.zscore('pcupdates', puzzle):
        #if not redisConnection.exists('pc:{puzzle}:0'.format(puzzle=puzzle)):
            # TODO: publish the job to the worker queue
            # Respond with 202
            
            # TODO: check redis memory usage and create cleanup job if it's past a threshold
            memory = redisConnection.info(section='memory')
            print('used_memory: {used_memory_human}'.format(**memory))
            maxmemory = memory.get('maxmemory')
            #maxmemory = 1024 * 2000
            if maxmemory != 0:
                target_memory = (maxmemory * 0.5)
                if memory.get('used_memory') > target_memory:
                    # push to queue for further processing
                    job = current_app.cleanupqueue.enqueue_call(
                        func='api.jobs.convertPiecesToDB.transferOldest', args=(target_memory,), result_ttl=0
                    )


            # For now just convert as it doesn't take long
            convert(puzzle)
        else:
            # The act of just loading the puzzle should update the pcupdates.
            # This will prevent the puzzle from being deleted by the janitor.
            redisConnection.zadd('pcupdates', puzzle, int(time.time()))


        query = """select id from Piece where (puzzle = :puzzle)"""
        (all_pieces, col_names) = rowify(cur.execute(query, {'puzzle': puzzle}).fetchall(), cur.description)

        # Create a pipe for buffering commands and disable atomic transactions
        pipe = redisConnection.pipeline(transaction=False)

        publicPieceProperties = ('x', 'y', 'rotate', 's', 'w', 'h', 'b')

        for item in all_pieces:
            piece = item.get('id')
            pipe.hmget('pc:{puzzle}:{piece}'.format(puzzle=puzzle, piece=piece), *publicPieceProperties)
        allPublicPieceProperties = pipe.execute()
        # convert the list of lists into list of dicts.  Only want to return the public piece props.
        pieces = map(lambda properties: dict(zip(publicPieceProperties, properties)), allPublicPieceProperties)
        for item in all_pieces:
            piece = item.get('id')
            pieces[piece]['id'] = piece

        pieceData = {
                'positions': pieces,
                'timestamp': '',
                }
        return encoder.encode(pieceData)
