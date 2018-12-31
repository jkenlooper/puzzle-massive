import datetime
import time
import uuid

from flask import current_app, make_response, request, abort, json, url_for
from flask.views import MethodView
from werkzeug.exceptions import HTTPException
import redis

from app import db
from database import fetch_query_string, rowify
from tools import formatPieceMovementString, formatBitMovementString, init_karma_key, get_public_karma_points

from constants import ACTIVE, IN_QUEUE, BUGGY_UNLISTED, POINT_COST_FOR_CHANGING_BIT, NEW_USER_STARTING_POINTS
#from jobs import pieceMove
from jobs import pieceTranslate
from user import user_id_from_ip, user_not_banned, increase_ban_time

redisConnection = redis.from_url('redis://localhost:6379/0/')
encoder = json.JSONEncoder(indent=2, sort_keys=True)

HOUR = 3600 # hour in seconds
MINUTE = 60 # minute in seconds

BLOCKEDPLAYER_EXPIRE_TIMEOUT = HOUR
MAX_KARMA = 25
MIN_KARMA = (int(MAX_KARMA/2) * -1) # -12
MOVES_BEFORE_PENALTY = 12
STACK_PENALTY = 1
HOTSPOT_EXPIRE = 30
HOTSPOT_LIMIT = 10
PIECE_MOVEMENT_RATE_TIMEOUT = 100
PIECE_MOVEMENT_RATE_LIMIT = 100

# How many pieces a user can move within this many seconds before being banned.
# Allow 30 pieces to be moved within 13 seconds. Exceeding that rate would
# probably imply that it is being scripted.
PIECE_TRANSLATE_RATE_TIMEOUT = 13
PIECE_TRANSLATE_MAX_COUNT = 30
PIECE_TRANSLATE_BAN_TIME_INCR = 60 * 5
PIECE_TRANSLATE_EXCEEDED_REASON = "Piece moves exceeded {PIECE_TRANSLATE_MAX_COUNT} in {PIECE_TRANSLATE_RATE_TIMEOUT} seconds".format(**locals())

TOKEN_EXPIRE_TIMEOUT = 60 * 5
TOKEN_LOCK_TIMEOUT = 5
TOKEN_INVALID_BAN_TIME_INCR = 15

def bump_count(user):
    """
    Bump the count for pieces moved for the user.
    The nginx conf has a 60r/m with a burst of 60 on this route. The goal here
    is to ban user if the piece movement rate continues to max out at this rate.
    """
    timestamp_now = int(time.time())
    rounded_timestamp = timestamp_now - (timestamp_now % PIECE_TRANSLATE_RATE_TIMEOUT)
    err_msg = {}

    # TODO: optimize the timestamp used here by truncating to last digits based
    # on the expiration of the key.
    piece_translate_rate_key = 'ptrate:{user}:{timestamp}'.format(user=user, timestamp=rounded_timestamp)
    if redisConnection.setnx(piece_translate_rate_key, 1):
        redisConnection.expire(piece_translate_rate_key, PIECE_TRANSLATE_RATE_TIMEOUT)
    count = redisConnection.incr(piece_translate_rate_key)
    if count > PIECE_TRANSLATE_MAX_COUNT:
        err_msg = increase_ban_time(user, PIECE_TRANSLATE_BAN_TIME_INCR)
        err_msg['reason'] = PIECE_TRANSLATE_EXCEEDED_REASON

    return err_msg

def get_blockedplayers_err_msg(expires, timeout):
    err_msg = {
        'msg': "Please wait.",
        'type': "blockedplayer",
        'reason': "Too many recent pieces moves from you were not helpful on this puzzle.",
        'expires': expires,
        'timeout': timeout
    }
    return err_msg

def get_too_many_pieces_in_proximity_err_msg(piece, piecesInProximity):
    err_msg = {
        'msg': "Piece move denied.",
        'type': "proximity",
        'reason': "Too many pieces within proximity of each other.",
        'piece': piece,
        'piecesInProximity': piecesInProximity
    }
    return err_msg

def get_puzzle_piece_token_key(puzzle, piece):
    return "pctoken:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece)

def get_puzzle_piece_token_queue_key(puzzle, piece):
    return "pqtoken:{puzzle}:{piece}".format(puzzle=puzzle, piece=piece)

class PaymentRequired(HTTPException):
    code = 402
    description = '<p>Payment required.</p>'

class PuzzlePieceTokenView(MethodView):
    """
    player gets token after mousedown.  /puzzle/<puzzle_id>/piece/<int:piece>/token/
    """
    decorators = [user_not_banned]

    def get(self, puzzle_id, piece):
        ip = request.headers.get('X-Real-IP')
        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(ip))
        mark = request.args.get('mark', '000')[:3]
        now = int(time.time())

        # Start db operations
        cur = db.cursor()
        # validate the puzzle_id
        result = cur.execute(fetch_query_string('select_puzzle_and_piece_status_for_token.sql'), {
            'puzzle_id': puzzle_id,
            'piece': piece
            }).fetchall()
        if not result:
            # 400 if puzzle does not exist or piece is not movable
            err_msg = {
                'msg': "piece can't be moved",
                'type': "immovable",
                'expires': now + 5,
                'timeout': 5
            }
            cur.close()
            return make_response(encoder.encode(err_msg), 400)
        (result, col_names) = rowify(result, cur.description)
        puzzle = result[0]['puzzle']

        piece_status = redisConnection.hget('pc:{puzzle}:{piece}'.format(puzzle=puzzle, piece=piece), 's')
        #print("ps {}".format(piece_status))
        if piece_status == '1':
            # immovable
            cur.close()
            err_msg = {
                'msg': "piece can't be moved",
                'type': "immovable",
                'expires': now + 5,
                'timeout': 5
            }
            return make_response(encoder.encode(err_msg), 400)


        blockedplayers_for_puzzle_key = 'blockedplayers:{puzzle}'.format(puzzle=puzzle)
        blockedplayers_expires = redisConnection.zscore(blockedplayers_for_puzzle_key, user)
        if blockedplayers_expires and blockedplayers_expires > now:
            err_msg = get_blockedplayers_err_msg(blockedplayers_expires, blockedplayers_expires - now)
            cur.close()
            return make_response(encoder.encode(err_msg), 429)

        puzzle_piece_token_key = get_puzzle_piece_token_key(puzzle, piece)

        # Check if player already has a token for this puzzle. This would mean
        # that the player tried moving another piece before the locked piece
        # finished moving.
        existing_token = redisConnection.get('token:{}'.format(user))
        if existing_token:
            (player_puzzle, player_piece, player_mark) = existing_token.split(':')
            player_puzzle = int(player_puzzle)
            player_piece = int(player_piece)
            if player_puzzle == puzzle:
                # Temporary ban the player when clicking a piece and not
                # dropping it before clicking another piece.
                if player_mark == mark:
                    # Ban the user for a few seconds
                    err_msg = increase_ban_time(user, TOKEN_LOCK_TIMEOUT)
                    err_msg['reason'] = "Concurrent piece movements on this puzzle from the same player are not allowed."
                    return make_response(encoder.encode(err_msg), 429)

                else:
                    # Block the player from selecting pieces on this puzzle
                    err_msg = {
                        'msg': "Please wait or do a different puzzle. New players on the same network will be sharing the same bit icon.  Please register as a separate player once enough dots are earned to select a new bit icon.",
                        'type': "sameplayerconcurrent",
                        'reason': "Concurrent piece movements on this puzzle from the same player are not allowed.",
                        'expires': now + TOKEN_LOCK_TIMEOUT,
                        'timeout': TOKEN_LOCK_TIMEOUT
                    }

                    uses_cookies = current_app.secure_cookie.get(u'ot')
                    if uses_cookies:
                        # Check if player has enough dots to generate a new
                        # player and if so add to err_msg to signal client to
                        # request a new player
                        dots = cur.execute("select points from User where id = :id and points >= :cost + :startpoints;", {'id': user, 'cost': POINT_COST_FOR_CHANGING_BIT, 'startpoints': NEW_USER_STARTING_POINTS}).fetchone()
                        if result:
                            err_msg['action'] = {
                                'msg': "Create a new player?",
                                'url': "/newapi{}".format(url_for('split-player'))
                            }
                        cur.close()
                    return make_response(encoder.encode(err_msg), 409)

        piece_token_queue_key = get_puzzle_piece_token_queue_key(puzzle, piece)
        queue_rank = redisConnection.zrank(piece_token_queue_key, user)

        if queue_rank == None:
            # Append this player to a queue for getting the next token. This
            # will prevent the player with the lock from continually locking the
            # same piece.
            redisConnection.zadd(piece_token_queue_key, user, now)
            queue_rank = redisConnection.zrank(piece_token_queue_key, user)
        redisConnection.expire(piece_token_queue_key, TOKEN_LOCK_TIMEOUT + 5)

        # Check if token on piece is in a queue and if the player requesting it
        # is the player that is next. Show an error message if not.
        if queue_rank > 0:
            err_msg = {
                'msg': "Another player is waiting to move this piece",
                'type': "piecequeue",
                'reason': 'Piece queue {}'.format(queue_rank),
                'expires': now + TOKEN_LOCK_TIMEOUT,
                'timeout': TOKEN_LOCK_TIMEOUT
            }
            cur.close()
            return make_response(encoder.encode(err_msg), 409)

        # Check if token on piece is still owned by another player
        existing_token_and_player = redisConnection.get(puzzle_piece_token_key)
        if existing_token_and_player:
            (other_token, other_player) = existing_token_and_player.split(':')
            puzzle_and_piece = redisConnection.get('token:{}'.format(other_player))
            # Check if there is a lock on this piece by other player
            if puzzle_and_piece:
                (other_puzzle, other_piece, other_mark) = puzzle_and_piece.split(':')
                other_puzzle = int(other_puzzle)
                other_piece = int(other_piece)
                if other_puzzle == puzzle and other_piece == piece and other_player != user:
                    # Other player has a lock on this piece
                    err_msg = {
                        'msg': "Another player is moving this piece",
                        'type': "piecelock",
                        'reason': 'Piece locked',
                        'expires': now + TOKEN_LOCK_TIMEOUT,
                        'timeout': TOKEN_LOCK_TIMEOUT
                    }
                    cur.close()
                    return make_response(encoder.encode(err_msg), 409)

        # Remove player from the piece token queue
        redisConnection.zrem(piece_token_queue_key, user)

        # This piece is up for grabs since it has been more then 5 seconds since
        # another player has grabbed it.
        token = uuid.uuid4().hex
        redisConnection.set(puzzle_piece_token_key, '{token}:{user}'.format(token=token, user=user), ex=TOKEN_EXPIRE_TIMEOUT)
        redisConnection.set('token:{}'.format(user), '{puzzle}:{piece}:{mark}'.format(puzzle=puzzle, piece=piece, mark=mark), ex=TOKEN_LOCK_TIMEOUT)

        # Claim the piece by showing the bit icon next to it.
        (x, y) = map(int, redisConnection.hmget('pc:{puzzle}:{piece}'.format(puzzle=puzzle, piece=piece), ['x', 'y']))
        msg = formatBitMovementString(user, x, y)
        redisConnection.publish(u'move:{0}'.format(puzzle_id), msg)

        response = {
            'token': token,
            'lock': now + TOKEN_LOCK_TIMEOUT,
            'expires': now + TOKEN_EXPIRE_TIMEOUT
        }
        cur.close()
        return encoder.encode(response)

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
        now = int(time.time())

        # validate the args and headers
        args = {}
        xhr_data = request.get_json()
        if xhr_data:
            args.update(xhr_data)
        if request.form:
            args.update(request.form.to_dict(flat=True))

        if len(args.keys()) == 0:
            err_msg = {
                'msg': "invalid args",
                'type': "invalid",
                'expires': now + 5,
                'timeout': 5
            }
            return make_response(encoder.encode(err_msg), 400)
        # check if args are only in acceptable set
        if len(self.ACCEPTABLE_ARGS.intersection(set(args.keys()))) != len(args.keys()):
            err_msg = {
                'msg': "invalid args",
                'type': "invalid",
                'expires': now + 5,
                'timeout': 5
            }
            return make_response(encoder.encode(err_msg), 400)
        # validate that all values are int
        for key, value in args.items():
            if not isinstance(value, int):
                try:
                    args[key] = int(value)
                except ValueError:
                    err_msg = {
                        'msg': "invalid args",
                        'type': "invalid",
                        'expires': now + 5,
                        'timeout': 5
                    }
                    return make_response(encoder.encode(err_msg), 400)

        # Start db operations
        cur = db.cursor()
        # validate the puzzle_id
        result = cur.execute(fetch_query_string('select_puzzle_id_by_puzzle_id.sql'), {
            'puzzle_id': puzzle_id
            }).fetchall()
        if not result:
            # 404 if puzzle does not exist
            cur.close()
            err_msg = {
                'msg': "Puzzle does not exist",
                'type': "missing",
                'expires': now + 5,
                'timeout': 5
            }
            return make_response(encoder.encode(err_msg), 404)
        (result, col_names) = rowify(result, cur.description)
        puzzle = result[0]['puzzle']

        # Token is to make sure puzzle is still in sync.
        # validate the token
        token = request.headers.get('Token')
        if not token:
            cur.close()
            err_msg = {
                'msg': "Missing token",
                'type': "missing",
                'expires': now + 5,
                'timeout': 5
            }
            return make_response(encoder.encode(err_msg), 400)
        puzzle_piece_token_key = get_puzzle_piece_token_key(puzzle, piece)
        # print("token key: {}".format(puzzle_piece_token_key))
        token_and_player = redisConnection.get(puzzle_piece_token_key)
        if token_and_player:
            player = int(user)
            (valid_token, other_player) = token_and_player.split(':')
            if token != valid_token:
                # print("token invalid {} != {}".format(token, valid_token))
                err_msg = increase_ban_time(user, TOKEN_INVALID_BAN_TIME_INCR)
                err_msg['reason'] = "Token is invalid"
                cur.close()
                return make_response(encoder.encode(err_msg), 409)
            if player != int(other_player):
                # print("player invalid {} != {}".format(player, other_player))
                err_msg = increase_ban_time(user, TOKEN_INVALID_BAN_TIME_INCR)
                err_msg['reason'] = "Player is invalid"
                cur.close()
                return make_response(encoder.encode(err_msg), 409)
        else:
            # Token has expired
            # print("token expired")
            err_msg = {
                'msg': "Token has expired",
                'type': "expiredtoken",
                'reason': ""
            }
            cur.close()
            return make_response(encoder.encode(err_msg), 409)

        # Expire the token at the lock timeout since it shouldn't be used again
        redisConnection.delete(puzzle_piece_token_key)
        redisConnection.delete('token:{}'.format(user))

        err_msg = bump_count(user)
        if err_msg.get('type') == "bannedusers":
            cur.close()
            return make_response(encoder.encode(err_msg), 429)


        result = cur.execute(fetch_query_string('select_puzzle_and_piece.sql'), {
            'puzzle_id': puzzle_id,
            'piece': piece
            }).fetchall()
        if not result:
            # 404 if puzzle or piece does not exist
            cur.close()
            err_msg = {
                'msg': "puzzle or piece not available",
                'type': "missing"
            }
            return make_response(encoder.encode(err_msg), 404)

        (result, col_names) = rowify(result, cur.description)
        puzzle_piece = result[0]

        # check if puzzle is in mutable state (not frozen)
        if not puzzle_piece['status'] in (ACTIVE, IN_QUEUE, BUGGY_UNLISTED):
            cur.close()
            err_msg = {
                'msg': "puzzle not in mutable state"
            }
            return make_response(encoder.encode(err_msg), 400)

        # check if piece can be moved
        pieceStatus = redisConnection.hget('pc:{puzzle}:{id}'.format(**puzzle_piece), 's')
        if pieceStatus == '1':
            # immovable
            cur.close()
            err_msg = {
                'msg': "piece can't be moved",
                'type': "immovable",
                'expires': now + 5,
                'timeout': 5
            }
            return make_response(encoder.encode(err_msg), 400)

        # check if piece will be moved to within boundaries
        if args.get('x') and (args['x'] < 0 or args['x'] > puzzle_piece['table_width']):
            #print("invalid move x: {0}".format(puzzle_piece.get('id')))
            cur.close()
            err_msg = {
                'msg': "Piece movement out of bounds",
                'type': "invalidpiecemove",
                'expires': now + 5,
                'timeout': 5
            }
            return make_response(encoder.encode(err_msg), 400)
        if args.get('y') and (args['y'] < 0 or args['y'] > puzzle_piece['table_height']):
            #print("invalid move y: {0}".format(puzzle_piece.get('id')))
            cur.close()
            err_msg = {
                'msg': "Piece movement out of bounds",
                'type': "invalidpiecemove",
                'expires': now + 5,
                'timeout': 5
            }
            return make_response(encoder.encode(err_msg), 400)

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
        #initial_karma = max(0, min(100/2, karma))
        karma_change = 0

        points_key = 'points:{user}'.format(user=user)

        # Decrease recent points if this is a new puzzle that user hasn't moved pieces on yet in the last hour
        pzrate_key = 'pzrate:{user}:{today}'.format(user=user, today=datetime.date.today().isoformat())
        if redisConnection.sadd(pzrate_key, puzzle) == 1:
            # New puzzle that player hasn't moved a piece on in the last hour.
            redisConnection.expire(pzrate_key, HOUR)
            recent_points = redisConnection.get(points_key) or 0
            if recent_points > 0:
                redisConnection.decr(points_key)

        # Decrease karma if piece movement rate has passed threshold
        # TODO: remove timestamp from key and depend on expire setting
        pcrate_key = 'pcrate:{puzzle}:{user}:{timestamp}'.format(puzzle=puzzle, user=user, timestamp=rounded_timestamp)
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
        # TODO: remove timestamp from key and depend on expire setting
        hotpc_key = 'hotpc:{puzzle}:{user}:{piece}:{timestamp}'.format(puzzle=puzzle, user=user, piece=piece, timestamp=rounded_timestamp)
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
            redisConnection.set(points_key, max(0, recent_points))
            if int(karma) + recent_points <= 0:
                expires = now + BLOCKEDPLAYER_EXPIRE_TIMEOUT
                blockedplayers_for_puzzle_key = 'blockedplayers:{puzzle}'.format(puzzle=puzzle)
                # Add the player to the blocked players list for the puzzle and
                # extend the expiration of the key.
                redisConnection.zadd(blockedplayers_for_puzzle_key, user, expires)
                redisConnection.expire(blockedplayers_for_puzzle_key, BLOCKEDPLAYER_EXPIRE_TIMEOUT)

                # Reset the karma for the player
                redisConnection.delete(karma_key)

                # TODO: drop these keys
                redisConnection.zadd('blockedplayers', '{ip}-{user}'.format(ip=ip, user=user), int(time.time()))
                redisConnection.zadd('blockedplayers:puzzle', '{ip}-{user}-{puzzle}'.format(ip=ip, user=user, puzzle=puzzle), int(recent_points))

                err_msg = get_blockedplayers_err_msg(expires, expires - now)
                err_msg['karma'] = get_public_karma_points(redisConnection, ip, user, puzzle)
                cur.close()
                return make_response(encoder.encode(err_msg), 429)

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
            err_msg = get_too_many_pieces_in_proximity_err_msg(piece, list(piecesInProximity))
            err_msg['karma'] = get_public_karma_points(redisConnection, ip, user, puzzle)

            cur.close()
            return make_response(encoder.encode(err_msg), 400)

        # Record hot spot (not exact)
        # TODO: remove timestamp from key and rely on expire setting
        rounded_timestamp_hotspot = timestamp_now - (timestamp_now % HOTSPOT_EXPIRE)
        hotspot_area_key = 'hotspot:{puzzle}:{user}:{timestamp}:{x}:{y}'.format(
            puzzle=puzzle, user=user, timestamp=rounded_timestamp_hotspot,
            x=int(x) - (int(x) % 200), y=int(y) - (int(y) % 200)
            )
        hotspot_count = redisConnection.incr(hotspot_area_key)
        if hotspot_count == 1:
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

        karma = get_public_karma_points(redisConnection, ip, user, puzzle)
        response = {
            'karma': karma,
            'karmaChange': karma_change,
            'id': piece
        }
        cur.close()
        return encoder.encode(response)

