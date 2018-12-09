import datetime
import time
import uuid

from flask import current_app, make_response, request, abort, json
from flask.views import MethodView
from werkzeug.exceptions import HTTPException
import redis

from app import db
from database import fetch_query_string, rowify
from tools import formatPieceMovementString, formatBitMovementString, init_karma_key

from constants import ACTIVE, IN_QUEUE, BUGGY_UNLISTED
#from jobs import pieceMove
from jobs import pieceTranslate
from user import user_id_from_ip, user_not_banned, increase_ban_time

redisConnection = redis.from_url('redis://localhost:6379/0/')
encoder = json.JSONEncoder(indent=2, sort_keys=True)

MAX_KARMA = 25
MIN_KARMA = (int(MAX_KARMA/2) * -1) # -12
MOVES_BEFORE_PENALTY = 12
STACK_PENALTY = 5
HOTSPOT_EXPIRE = 30
HOTSPOT_LIMIT = 10
PIECE_MOVEMENT_RATE_TIMEOUT = 100
PIECE_MOVEMENT_RATE_LIMIT = 100
HOUR = 3600 # hour in seconds
MINUTE = 60 # minute in seconds
TWO_HOURS = 7200

# How many pieces a user can move within this many seconds before being banned.
# Allow 30 pieces to be moved within 13 seconds. Exceeding that rate would
# probably imply that it is being scripted.
PIECE_TRANSLATE_RATE_TIMEOUT = 13
PIECE_TRANSLATE_MAX_COUNT = 30
PIECE_TRANSLATE_BAN_TIME_INCR = 60 * 5

def bump_count(ip, user):
    """
    Bump the count for pieces moved for the user.
    The nginx conf has a 60r/m with a burst of 60 on this route. The goal here
    is to ban user if the piece movement rate continues to max out at this rate.
    """
    timestamp_now = int(time.time())
    rounded_timestamp = timestamp_now - (timestamp_now % PIECE_TRANSLATE_RATE_TIMEOUT)

    piece_translate_rate_key = 'ptrate:{ip}:{user}:{timestamp}'.format(ip=ip, user=user, timestamp=rounded_timestamp)
    if redisConnection.setnx(piece_translate_rate_key, 1):
        redisConnection.expire(piece_translate_rate_key, PIECE_TRANSLATE_RATE_TIMEOUT)
    count = redisConnection.incr(piece_translate_rate_key)
    if count > PIECE_TRANSLATE_MAX_COUNT:
        increase_ban_time(ip, user, PIECE_TRANSLATE_BAN_TIME_INCR)



def get_puzzle_piece_token_key(puzzle, piece):
    return "pctoken:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece)

class PaymentRequired(HTTPException):
    code = 402
    description = '<p>Payment required.</p>'

class PuzzlePieceTokenView(MethodView):
    """
    player gets token after mousedown.  /puzzle/<puzzle_id>/piece/<int:piece>/token/<int:player>/
    """
    decorators = [user_not_banned]

    def get(self, puzzle_id, piece, player):
        ip = request.headers.get('X-Real-IP')
        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(ip))

        # Validate the user
        if user != player:
            abort(403)

        # Start db operations
        c = db.cursor()
        # validate the puzzle_id
        result = c.execute(fetch_query_string('select_puzzle_id_by_puzzle_id.sql'), {
            'puzzle_id': puzzle_id
            }).fetchall()
        if not result:
            # 404 if puzzle does not exist
            abort(404)
        (result, col_names) = rowify(result, c.description)
        puzzle = result[0]['puzzle']

        puzzle_piece_token_key = get_puzzle_piece_token_key(puzzle, piece)

        # Check if token on piece is still owned by another player
        existing_token_and_player = redisConnection.get(puzzle_piece_token_key)
        if existing_token_and_player:
            (other_token, other_player) = existing_token_and_player.split(':')
            puzzle_and_piece = redisConnection.get('token:{}'.format(other_player))
            if puzzle_and_piece:
                (other_puzzle, other_piece) = puzzle_and_piece.split(':')
                if other_puzzle == puzzle and other_piece == piece and other_player != player:
                    # Player needs to wait before moving this piece
                    print("Player needs to wait before moving this piece {}, {}, {}".format(other_puzzle, other_piece, other_player))
                    abort(409)

        # This piece is up for grabs since it has been more then 5 seconds since
        # another player has grabbed it.
        token = uuid.uuid4().hex
        redisConnection.set(puzzle_piece_token_key, '{token}:{player}'.format(token=token, player=player), ex=60) # TODO: set to 5 minutes timeout
        redisConnection.set('token:{}'.format(player), '{puzzle}:{piece}'.format(puzzle=puzzle, piece=piece), ex=5)

        response = {
            'token': token,
            'lock': int(time.time() + 5),
            'expires': int(time.time() + 60) # TODO: set to 5 minutes
        }
        return encoder.encode(response)

        #/token/ GET returns a generated token and also stores it temporarily in redis. It also updates the value in token:{player}.
        #The piece is owned for a limited time by the player.  Other players will get a response status code to wait.
        #key: pctoken:{puzzle}:{piece}
        #value: asdf1234:{player}
        #expires: 5 minutes

        #Only allow 1 piece to be locked per player.  This shows that the player has a token for the given puzzle and piece and has control over it (locked).
        #key: token:{player}
        #value: {puzzle}:{piece}
        #expires: 5seconds

        #Remove any other pctoken:... that the player has acquired

class PuzzlePiecesMovePublishView(MethodView):
    """
    Publish the puzzle piece movement and push it to the redis queue.

    * Check if valid args
    * Validate the token
    * Validate that puzzle and piece exist and are in mutable state

    * Set karma

    * Check if piece move is within bounds
    * Check if piece move is not to a large stacked area

    * Check if karma + points > 0

    * Publish bit movment
    * Start piece translate logic

    Return karma amount
    """
    decorators = [user_not_banned]
    ACCEPTABLE_ARGS = set(['x', 'y', 'r'])

    def patch(self, puzzle_id, piece):
        """
        args:
        x
        y
        r
        """
        ip = request.headers.get('X-Real-IP')
        user = current_app.secure_cookie.get(u'user') or user_id_from_ip(ip)

        # validate the args and headers
        args = {}
        xhr_data = request.get_json()
        if xhr_data:
            args.update(xhr_data)
        if request.form:
            args.update(request.form.to_dict(flat=True))

        if len(args.keys()) == 0:
            abort(400)
        # check if args are only in acceptable set
        if len(self.ACCEPTABLE_ARGS.intersection(set(args.keys()))) != len(args.keys()):
            abort(400)
        # validate that all values are int
        for key, value in args.items():
            if not isinstance(value, int):
                try:
                    args[key] = int(value)
                except ValueError:
                    abort(400)

        # Start db operations
        c = db.cursor()
        # validate the puzzle_id
        result = c.execute(fetch_query_string('select_puzzle_id_by_puzzle_id.sql'), {
            'puzzle_id': puzzle_id
            }).fetchall()
        if not result:
            # 404 if puzzle does not exist
            abort(404)
        (result, col_names) = rowify(result, c.description)
        puzzle = result[0]['puzzle']

        # Token is to make sure puzzle is still in sync.
        # validate the token
        token = request.headers.get('Token')
        if not token:
            abort(403)
        puzzle_piece_token_key = get_puzzle_piece_token_key(puzzle, piece)
        print("token key: {}".format(puzzle_piece_token_key))
        token_and_player = redisConnection.get(puzzle_piece_token_key)
        if token_and_player:
            player = int(user)
            (valid_token, other_player) = token_and_player.split(':')
            if token != valid_token:
                print("token invalid {} != {}".format(token, valid_token))
                abort(409)
            if player != int(other_player):
                print("player invalid {} != {}".format(player, other_player))
                abort(409)
        else:
            # Token has expired
            print("token expired")
            abort(409)

        bump_count(ip, user)

        result = c.execute(fetch_query_string('select_puzzle_and_piece.sql'), {
            'puzzle_id': puzzle_id,
            'piece': piece
            }).fetchall()
        if not result:
            # 404 if puzzle or piece does not exist
            abort(404)

        (result, col_names) = rowify(result, c.description)
        puzzle_piece = result[0]

        # check if puzzle is in mutable state (not frozen)
        if not puzzle_piece['status'] in (ACTIVE, IN_QUEUE, BUGGY_UNLISTED):
            abort(400)

        # check if piece can be moved
        pieceStatus = redisConnection.hget('pc:{puzzle}:{id}'.format(**puzzle_piece), 's')
        if pieceStatus == '1':
            # immovable
            abort(400)

        # check if piece will be moved to within boundaries
        if args.get('x') and (args['x'] < 0 or args['x'] > puzzle_piece['table_width']):
            #print("invalid move x: {0}".format(puzzle_piece.get('id')))
            abort(400)
        if args.get('y') and (args['y'] < 0 or args['y'] > puzzle_piece['table_height']):
            #print("invalid move y: {0}".format(puzzle_piece.get('id')))
            abort(400)

        x = str(args.get('x', ''))
        y = str(args.get('y', ''))
        r = str(args.get('r', ''))
        puzzle = puzzle_piece['puzzle']

        # Set the rounded timestamp
        timestamp_now = int(time.time())
        rounded_timestamp = timestamp_now - (timestamp_now % PIECE_MOVEMENT_RATE_TIMEOUT)

        # Update karma
        karma_key = init_karma_key(redisConnection, puzzle, ip)
        # Set a limit to minimum karma so other players on the network can still play
        karma = max(MIN_KARMA, int(redisConnection.get(karma_key)))
        initial_karma = max(0, min(100/2, karma))
        karma_change = 0

        points_key = 'points:{user}'.format(user=user)

        # Decrease recent points if this is a new puzzle that ip hasn't moved pieces on yet in the last hour
        pzrate_key = 'pzrate:{ip}:{today}'.format(ip=ip, today=datetime.date.today().isoformat())
        if redisConnection.sadd(pzrate_key, puzzle) == 1:
            # New puzzle that player hasn't moved a piece on in the last hour.
            redisConnection.expire(pzrate_key, HOUR)
            redisConnection.decr(points_key)

        # Decrease karma if piece movement rate has passed threshold
        pcrate_key = 'pcrate:{puzzle}:{ip}:{timestamp}'.format(puzzle=puzzle, ip=ip, timestamp=rounded_timestamp)
        if redisConnection.setnx(pcrate_key, 1):
            redisConnection.expire(pcrate_key, PIECE_MOVEMENT_RATE_TIMEOUT)
        else:
            moves = redisConnection.incr(pcrate_key)
            if moves > PIECE_MOVEMENT_RATE_LIMIT:
                # print 'decrease because piece movement rate limit reached.'
                if karma > MIN_KARMA:
                    karma = redisConnection.decr(karma_key)
                karma_change -= 1

        # Decrease karma when moving the same piece again within a minute
        hotpc_key = 'hotpc:{puzzle}:{ip}:{piece}:{timestamp}'.format(puzzle=puzzle, ip=ip, piece=piece, timestamp=rounded_timestamp)
        recent_move_count = redisConnection.incr(hotpc_key)
        if recent_move_count == 1:
            redisConnection.expire(hotpc_key, PIECE_MOVEMENT_RATE_TIMEOUT)

        if recent_move_count > MOVES_BEFORE_PENALTY:
            if karma > MIN_KARMA:
                karma = redisConnection.decr(karma_key)
            karma_change -= 1


        if int(karma) <= 0:
            # Decrease recent points for a piece move that decreased karma
            recent_points = redisConnection.decr(points_key, amount=abs(karma_change)) if karma_change < 0 else int(redisConnection.get(points_key) or 0)
            if int(karma) + recent_points <= 0:
                redisConnection.zadd('blockedplayers', '{ip}-{user}'.format(ip=ip, user=user), int(time.time()))
                redisConnection.zadd('blockedplayers:puzzle', '{ip}-{user}-{puzzle}'.format(ip=ip, user=user, puzzle=puzzle), int(recent_points))
                # print '{}, {}'.format(karma, recent_points)
                return make_response(
                    '{}'.format(karma + recent_points)
                    , 429)


                #abort(429)


        # Check if there are too many pieces stacked. Slightly less exact from
        # what pieceTranslate does.  This includes immovable pieces, and the
        # pieces own group which would normally be filtered out when checking
        # if the piece can be joined.
        (pieceWidth, pieceHeight) = map(int, redisConnection.hmget('pc:{puzzle}:{piece}'.format(puzzle=puzzle, piece=piece), ['w', 'h']))
        toleranceX = min(pieceWidth, 200)
        toleranceY = min(pieceHeight, 200)
        proximityX = set(map(int, redisConnection.zrangebyscore('pcx:{puzzle}'.format(puzzle=puzzle), int(x) - toleranceX, int(x) + toleranceX)))
        proximityY = set(map(int, redisConnection.zrangebyscore('pcy:{puzzle}'.format(puzzle=puzzle), int(y) - toleranceY, int(y) + toleranceY)))
        piecesInProximity = set.intersection(proximityX, proximityY)
        #print("{0} {1} {2}".format(len(piecesInProximity), x, y))
        if len(piecesInProximity) >= 13:
            if karma > MIN_KARMA:
                karma = redisConnection.decr(karma_key, amount=STACK_PENALTY)
            abort(400)

        # Record hot spot (not exact)
        rounded_timestamp_hotspot = timestamp_now - (timestamp_now % HOTSPOT_EXPIRE)
        hotspot_area_key = 'hotspot:{puzzle}:{ip}:{timestamp}:{x}:{y}'.format(
            puzzle=puzzle, ip=ip, timestamp=rounded_timestamp_hotspot,
            x=int(x) - (int(x) % 200), y=int(y) - (int(y) % 200)
            )
        hotspot_count = redisConnection.incr(hotspot_area_key)
        if hotspot_count == 1:
            # print 'set hotspot count expire'
            redisConnection.expire(hotspot_area_key, HOTSPOT_EXPIRE)
        if hotspot_count > HOTSPOT_LIMIT:
            if karma > MIN_KARMA:
                karma = redisConnection.decr(karma_key)
            karma_change -= 1

        # publish just the bit movement so it matches what this player did
        msg = formatPieceMovementString(piece, x, y, r, '', '')
        if user != None:
            #msg = msg + '\n' + formatBitMovementString(user, x, y)
            msg = formatBitMovementString(user, x, y)
        redisConnection.publish(u'move:{0}'.format(puzzle_id), msg)

        # push to queue for further processing
        #job = current_app.queue.enqueue_call(
        #    func='api.jobs.pieceTranslate.translate', args=(ip, user, puzzle_piece, piece, args.get('x'), args.get('y'), args.get('r'), karma_change), result_ttl=0, timeout=2, ttl=3
        #)
        (topic, msg, karma_change) = pieceTranslate.translate(ip, user, puzzle_piece, piece, args.get('x'), args.get('y'), args.get('r'), karma_change)

        karma_change = False if karma_change == 0 else karma_change

        recent_points = min(100/2, int(redisConnection.get(points_key) or 0))
        karma = min(100/2, int(redisConnection.get(karma_key)))
        karma = max(0, min(100/2, karma + recent_points))
        # print '{}, {}'.format(karma, karma_change)
        response = {
            'karma': karma * 2,
            'karmaChange': karma_change,
            'id': piece
        }
        return encoder.encode(response)
