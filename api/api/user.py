from __future__ import division
from builtins import str, bytes
from past.utils import old_div
import crypt
import string
import random
import time
import datetime
import hashlib

from flask import current_app, json, redirect, make_response, request
from flask.views import MethodView
import redis

from api.app import db
from api.database import rowify, fetch_query_string
from api.constants import POINT_COST_FOR_CHANGING_BIT, NEW_USER_STARTING_POINTS

LETTERS = '%s%s' % (string.ascii_letters, string.digits)

ANONYMOUS_USER_ID = 2

LITTLE_LESS_THAN_A_WEEK = (60 * 60 * 24 * 7) - random.randint(3023, 3600 * 14)
LITTLE_MORE_THAN_A_DAY = (60 * 60 * 24) + random.randint(3023, 3600 * 14)
MAX_BAN_TIME = LITTLE_LESS_THAN_A_WEEK
HONEY_POT_BAN_TIME = LITTLE_MORE_THAN_A_DAY

# after 14 days reset the expiration date of the cookie by setting will_expire_cookie
OLD_QUERY_USER_DETAILS = """select login, icon, score, points as dots, id, cookie_expires,
  strftime('%s', cookie_expires) <= strftime('%s', 'now', '+351 days') as will_expire_cookie
  from User where id = :id;"""

QUERY_USER_DETAILS = """
SELECT u.login, b.name AS icon, u.score, u.points as dots, u.id, u.cookie_expires,
strftime('%s', u.cookie_expires) <= strftime('%s', 'now', '+351 days') as will_expire_cookie,
strftime('%s', b.expiration) <= strftime('%s', 'now') as bit_expired
FROM User AS u
LEFT OUTER JOIN BitIcon AS b ON u.id = b.user
WHERE u.id = :id;
"""


EXTEND_COOKIE_QUERY = """
update User set cookie_expires = strftime('%Y-%m-%d', 'now', '+365 days') where id = :id;
"""

QUERY_SET_PASSWORD = """update User set password = :password where id = :id"""
QUERY_USER_LOGIN = """select login from User where id = :id"""

QUERY_USER_ID_BY_IP = """
select id from User where ip = :ip and cookie_expires isnull limit 1;
"""
QUERY_USER_ID_BY_LOGIN = """
select id from User where ip = :ip and login = :login;
"""

redisConnection = redis.from_url('redis://localhost:6379/0/', decode_responses=True)
encoder = json.JSONEncoder(indent=2, sort_keys=True)

def generate_password():
    "Create a random string for use as password. Return as cleartext and encrypted."
    timestamp = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
    random_int = random.randint(1, 99999)
    p_string = hashlib.sha224(bytes("%s%i" % (timestamp, int(old_div(random_int,2))), 'utf-8')).hexdigest()[:13]
    salt = '%s%s' % (random.choice(LETTERS), random.choice(LETTERS))
    password = crypt.crypt(p_string, salt)

    return (p_string, password)

def generate_user_login():
    "Create a unique login"
    timestamp = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
    random_int = random.randint(1, 99999)
    login = hashlib.sha224(bytes("%s%i" % (timestamp, random_int), 'utf-8')).hexdigest()[:13]

    return login

def user_id_from_ip(ip, skip_generate=False):
    cur = db.cursor()

    result = cur.execute(QUERY_USER_ID_BY_IP, {'ip':ip}).fetchall()
    user_id = ANONYMOUS_USER_ID

    # No ip in db so create it except if the skip_generate flag is set
    if not result:
        if skip_generate:
            return None
        login = generate_user_login()
        query = """insert into User (points, score, login, m_date, ip) values
                (:points, 0, :login, datetime('now'), :ip)"""
        cur.execute(query, {'ip': ip, 'login': login, 'points': NEW_USER_STARTING_POINTS})
        db.commit()

        result = cur.execute(QUERY_USER_ID_BY_LOGIN, {'ip':ip, 'login':login}).fetchall()
        (result, col_names) = rowify(result, cur.description)
        user_id = result[0]['id']

        # Claim a random bit icon
        cur.execute(fetch_query_string('claim_random_bit_icon.sql'), {'user': user_id})
        db.commit()
    else:
        (result, col_names) = rowify(result, cur.description)
        user_id = result[0]['id']

    cur.close()
    return user_id

def user_not_banned(f):
    """Check if the user is not banned and respond with 429 if so"""
    def decorator(*args, **kwargs):
        ip = request.headers.get('X-Real-IP')
        user = current_app.secure_cookie.get(u'user') or user_id_from_ip(ip, skip_generate=True)
        if not user == None:
            user = int(user)
            banneduser_score = redisConnection.zscore('bannedusers', user)
            if banneduser_score:
                now = int(time.time())
                if banneduser_score > now:
                    # The user could be banned for many different reasons.  Most
                    # bans only last for a few seconds because of recent piece
                    # movements.
                    response = ". . . please wait . . ."
                    if 'application/json' in request.headers.get('Accept'):
                        response = encoder.encode({
                            'msg': response,
                            'expires': banneduser_score,
                            'timeout': banneduser_score - now
                        })
                    return make_response(response, 429)

        return f(*args, **kwargs)
    return decorator

def increase_ban_time(user, seconds):
    now = int(time.time())
    current = int(redisConnection.zscore('bannedusers', user) or now)
    current = max(current, now)
    ban_timestamp = min(current + seconds, now + MAX_BAN_TIME)
    redisConnection.zadd('bannedusers', {user: ban_timestamp})
    return {
        'msg': "Temporarily banned. Ban time has increased by {} seconds".format(seconds),
        'type': "bannedusers",
        'user': user,
        'expires': ban_timestamp,
        'timeout': ban_timestamp - now
    }

class CurrentUserIDView(MethodView):
    """
    Current user based on secure user cookie.
    """
    decorators = [user_not_banned]

    def get(self):
        "return the user id by secure cookie or by ip."
        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP')))
        return str(user)

class GenerateAnonymousLogin(MethodView):
    """
    A new password is generated with the existin user login as an anonymous
    login link which the player will need to copy in order to login after the
    cookie expires.
    """
    decorators = [user_not_banned]

    def get(self):
        "Return an object to be used by the generateBitLink js call"

        user = current_app.secure_cookie.get(u'user')
        if user is None:
            return make_response('no user', 403)
        user = int(user)

        (p_string, password) = generate_password()

        # Store encrypted password in db
        cur = db.cursor()
        try:
            result = cur.execute(QUERY_USER_LOGIN, {'id':user}).fetchall()
        except IndexError:
            # user may have been added after a db rollback
            return make_response('no user', 404)

        if not result:
            return make_response('no user', 404)

        (result, col_names) = rowify(result, cur.description)
        user_data = result[0]

        cur.execute(QUERY_SET_PASSWORD, {'id':user, 'password':password})
        db.commit()

        cur.close()
        data = {'bit':"".join(["", "/puzzle-api/bit/", user_data['login'], p_string])}
        return encoder.encode(data)

class UserLoginView(MethodView):
    """
    To maintain backwards compatibility this is rewritten in nginx from /puzzle-api/bit/<bitLink>
    """

    def get(self, anonymous_login):
        "Set the user cookie if correct anon bit link."
        user = anonymous_login[:13]
        password = anonymous_login[13:]
        cur = db.cursor()

        response = make_response(redirect('/'))

        query = """select * from User where login = :user"""
        result = cur.execute(query, {'user':user}).fetchall()

        if not result:
            return make_response('no user', 404)

        (result, col_names) = rowify(result, cur.description)
        user_data = result[0]

        if crypt.crypt(password, user_data['password']) == user_data['password']:
            current_app.secure_cookie.set(u'user', str(user_data['id']), response, expires_days=365)
            cur.execute(EXTEND_COOKIE_QUERY, {'id': user_data['id']})
            db.commit()
        else:
            # Invalid anon login; delete cookie just in case it's there
            expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
            current_app.secure_cookie.set(u'user', "", response, expires=expires)

        cur.close()

        return response

class UserLogoutView(MethodView):
    """
    Deleting the user cookie will logout the user
    """
    decorators = [user_not_banned]

    def get(self):
        "Delete the cookie by setting the expires to the past."
        response = make_response(redirect('/'))
        expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
        current_app.secure_cookie.set(u'user', "", response, expires=expires)

        return response


class UserDetailsView(MethodView):
    """
    """
    decorators = [user_not_banned]

    def get(self):
        response = make_response(redirect('/'))

        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP')))

        cur = db.cursor()

        try:
            result = cur.execute(QUERY_USER_DETAILS, {'id':user}).fetchall()
        except IndexError:
            # user may have been added after a db rollback
            return make_response('no user', 404)

        if not result:
            return make_response('no user', 404)

        (result, col_names) = rowify(result, cur.description)
        user_details = result[0]

        if user_details['will_expire_cookie'] == 1:
            # extend the cookie
            current_app.secure_cookie.set(u'user', str(user_details['id']), response, expires_days=365)
            cur.execute(EXTEND_COOKIE_QUERY, {'id': user_details['id']})
            db.commit()
        del user_details['will_expire_cookie']

        # TODO: Include available puzzle instance slot count and list of puzzle
        # instances this player has.

        cur.close()

        return encoder.encode(user_details)

class ClaimRandomBit(MethodView):
    """
    Claim a random bit icon only when a user doesn't have an icon.
    """
    decorators = [user_not_banned]

    def post(self):
        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP')))

        cur = db.cursor()

        try:
            result = cur.execute(QUERY_USER_DETAILS, {'id':user}).fetchall()
        except IndexError:
            # user may have been added after a db rollback
            return make_response('no user', 404)

        if not result:
            return make_response('no user', 404)

        (result, col_names) = rowify(result, cur.description)
        user_details = result[0]

        if user_details['icon']:
            return make_response('icon', 400)

        cur.execute(fetch_query_string('claim_random_bit_icon.sql'), {'user': user})
        db.commit()

        cur.close()

        return ''

class SplitPlayer(MethodView):
    """
    Called when multiple users on the same network happen to all have the same
    player.  This will split that player login into another new one which the
    user calling it will then own.
    """
    decorators = [user_not_banned]

    def post(self):
        # Prevent creating a new user if no support for cookies. Player should
        # have 'ot' already set by viewing the page.
        uses_cookies = current_app.secure_cookie.get(u'ot')
        if not uses_cookies:
            return make_response('no cookies', 400)

        ip = request.headers.get('X-Real-IP')
        # Verify user is logged in
        user = current_app.secure_cookie.get(u'user') or user_id_from_ip(ip, skip_generate=True)
        if user is None:
            return make_response('not logged in', 400)
        user = int(user)

        response = make_response('', 200)

        cur = db.cursor()

        # Update user points for changing bit icon
        # TODO: what prevents a player from creating a lot of splits?
        result = cur.execute("select points from User where id = :id and points >= :cost + :startpoints;", {'id': user, 'cost': POINT_COST_FOR_CHANGING_BIT, 'startpoints': NEW_USER_STARTING_POINTS}).fetchone()
        if not result:
            return make_response('not enough dots', 400)
        cur.execute("update User set points = points - :cost where id = :id;", {'id': user, 'cost': POINT_COST_FOR_CHANGING_BIT})

        # Create new user

        login = generate_user_login()
        (p_string, password) = generate_password()

        query = """
        insert into User
        (password, m_date, cookie_expires, points, score, login, ip) values
        (:password, datetime('now'), strftime('%Y-%m-%d', 'now', '+365 days'), :points, 0, :login, :ip);
        """
        cur.execute(query, {'password': password, 'ip': ip, 'points': NEW_USER_STARTING_POINTS, 'login': login})

        result = cur.execute(QUERY_USER_ID_BY_LOGIN, {'ip':ip, 'login':login}).fetchall()
        (result, col_names) = rowify(result, cur.description)
        newuser = result[0]['id']

        current_app.secure_cookie.set(u'user', str(newuser), response, expires_days=365)

        # Claim a random bit icon
        cur.execute(fetch_query_string('claim_random_bit_icon.sql'), {'user': newuser})

        db.commit()

        cur.close()
        return response

class AdminBlockedPlayersList(MethodView):
    """
    ip:
        user:
            timestamp:
            recent_points:
            puzzles: []
    """
    def get(self):
        blocked = {
        }

        blockedplayers = redisConnection.zrevrange('blockedplayers', 0, -1, withscores=True)
        blockedplayers_puzzle = redisConnection.zrange('blockedplayers:puzzle', 0, -1, withscores=True)

        # Add ip -> user -> timestamp
        for (ip_user, timestamp) in blockedplayers:
            (ip, user) = ip_user.split('-')
            if not blocked.get(ip):
                blocked[ip] = {}
            blocked[ip][user] = {
                'timestamp': timestamp
            }

        # Set puzzles and recent points
        for (ip_user_puzzle, recent_points) in blockedplayers_puzzle:
            (ip, user, puzzle) = ip_user_puzzle.split('-')
            if not blocked[ip][user].get('puzzles'):
                blocked[ip][user]['puzzles'] = []
            blocked[ip][user]['puzzles'].append({'puzzle': puzzle, 'points': recent_points})
            # sorted by asc so the last will be the highest
            blocked[ip][user]['recent_points'] = recent_points

        return encoder.encode(blocked)


class AdminBannedUserList(MethodView):
    """
    user:
        timestamp:
    """
    def get(self):
        banned = {}

        bannedusers = redisConnection.zrevrangebyscore('bannedusers', '+inf', int(time.time()), withscores=True)

        # Add user -> timestamp
        for (user, timestamp) in bannedusers:
            banned[user] = {
                'timestamp': timestamp
            }

        return encoder.encode(banned)

    def post(self):
        "Cleanup banned users"

        # clean up old banned users if any
        old_bannedusers_count = redisConnection.zremrangebyscore('bannedusers', 0, now)
        return old_bannedusers_count

class BanishSelf(MethodView):
    """
    Adds the ip and user id for the user calling it to the bannedusers list with
    the timestamp of when the ban will be lifted.
    """
    decorators = [user_not_banned]
    response_text = "Press any key to continue . . ."

    def get(self):
        "The url for this is listed in robots.txt under a Disallow"
        ip = request.headers.get('X-Real-IP')
        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(ip))
        increase_ban_time(user, HONEY_POT_BAN_TIME)

        return make_response(self.response_text, 201)

    def post(self):
        "User filled out and submitted the hidden form.  Most likely a spam bot."
        ip = request.headers.get('X-Real-IP')
        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(ip))

        increase_ban_time(user, HONEY_POT_BAN_TIME)
        return make_response(self.response_text, 201)
