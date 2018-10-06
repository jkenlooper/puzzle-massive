import crypt
import string
import random
import time
import datetime
import hashlib

from flask import current_app, abort, json, redirect, make_response, request
from flask.views import MethodView
import redis

from api.app import db
from api.database import rowify, fetch_query_string

LETTERS = '%s%s' % (string.ascii_letters, string.digits)

ANONYMOUS_USER_ID = 2

NEW_USER_STARTING_POINTS = 1300

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

redisConnection = redis.from_url('redis://localhost:6379/0/')
encoder = json.JSONEncoder(indent=2, sort_keys=True)

def generate_password():
    "Create a random string for use as password. Return as cleartext and encrypted."
    timestamp = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
    random_int = random.randint(1, 99999)
    p_string = hashlib.sha224("%s%i" % (timestamp, int(random_int/2))).hexdigest()[:13]
    salt = '%s%s' % (random.choice(LETTERS), random.choice(LETTERS))
    password = crypt.crypt(p_string, salt)

    return (p_string, password)

def generate_user_login():
    "Create a unique login"
    timestamp = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
    random_int = random.randint(1, 99999)
    login = hashlib.sha224("%s%i" % (timestamp, random_int)).hexdigest()[:13]

    return login

def user_id_from_ip(ip):
    QUERY_USER_ID_BY_IP = """
    select id from User where ip = :ip and cookie_expires isnull limit 1;
    """
    QUERY_USER_ID_BY_LOGIN = """
    select id from User where ip = :ip and login = :login;
    """
    cur = db.cursor()

    result = cur.execute(QUERY_USER_ID_BY_IP, {'ip':ip}).fetchall()
    user_id = ANONYMOUS_USER_ID

    # No ip in db so create it
    if not result:
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

    return str(user_id)

class CurrentUserIDView(MethodView):
    """
    Current user based on secure user cookie.
    """
    def get(self):
        "return the user id by secure cookie or by ip."
        user = current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP'))
        return user

class GenerateAnonymousLogin(MethodView):
    """
    A new password is generated with the existin user login as an anonymous
    login link which the player will need to copy in order to login after the
    cookie expires.
    """
    def get(self):
        "Return an object to be used by the generateBitLink js call"

        user = current_app.secure_cookie.get(u'user')
        if user is None:
            abort(403)

        (p_string, password) = generate_password()

        # Store encrypted password in db
        cur = db.cursor()
        try:
            result = cur.execute(QUERY_USER_LOGIN, {'id':int(user)}).fetchall()
        except IndexError:
            # user may have been added after a db rollback
            abort(404)

        if not result:
            abort(404)

        (result, col_names) = rowify(result, cur.description)
        user_data = result[0]

        cur.execute(QUERY_SET_PASSWORD, {'id':int(user), 'password':password})
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
            abort(404)

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
    def get(self):
        "Delete the cookie by setting the expires to the past."
        response = make_response(redirect('/'))
        expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
        current_app.secure_cookie.set(u'user', "", response, expires=expires)

        return response


class UserDetailsView(MethodView):
    """
    """
    def get(self):
        response = make_response(redirect('/'))

        # Verify user is logged in
        user = current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP'))
        if user is None:
            abort(403)

        cur = db.cursor()

        try:
            result = cur.execute(QUERY_USER_DETAILS, {'id':int(user)}).fetchall()
        except IndexError:
            # user may have been added after a db rollback
            abort(404)

        if not result:
            abort(404)

        (result, col_names) = rowify(result, cur.description)
        user_details = result[0]

        if user_details['will_expire_cookie'] == 1:
            # extend the cookie
            current_app.secure_cookie.set(u'user', str(user_details['id']), response, expires_days=365)
            cur.execute(EXTEND_COOKIE_QUERY, {'id': user_details['id']})
            db.commit()
        del user_details['will_expire_cookie']
        cur.close()

        return encoder.encode(user_details)

class ClaimRandomBit(MethodView):
    """
    Claim a random bit icon only when a user doesn't have an icon.
    """
    def post(self):
        # Verify user is logged in
        user = current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP'))
        if user is None:
            abort(400)

        cur = db.cursor()

        try:
            result = cur.execute(QUERY_USER_DETAILS, {'id':int(user)}).fetchall()
        except IndexError:
            # user may have been added after a db rollback
            abort(404)

        if not result:
            abort(404)

        (result, col_names) = rowify(result, cur.description)
        user_details = result[0]

        if user_details['icon']:
            abort(400)

        cur.execute(fetch_query_string('claim_random_bit_icon.sql'), {'user': int(user)})
        db.commit()

        cur.close()

        return ''


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
