from builtins import str
from random import randint
import datetime

from flask import current_app, abort, json, redirect, make_response, request
from flask.views import MethodView

from api.app import db
from api.database import rowify, fetch_query_string
from api.user import generate_password, generate_user_login, user_id_from_ip, user_not_banned
from api.constants import POINT_COST_FOR_CHANGING_BIT, NEW_USER_STARTING_POINTS

encoder = json.JSONEncoder(indent=2, sort_keys=True)

QUERY_BITICON_BY_USER = """
SELECT u.id, b.name AS icon
  FROM BitIcon AS b
  JOIN User AS u ON u.id = b.user
WHERE u.id = :user;
"""

class BitIconView(MethodView):
    """user id to bit icon name"""
    decorators = [user_not_banned]

    def get(self, user_id):
        "JSON object with icon"

        # Set the default to show no icon
        user_data = {
                'id': int(user_id),
                'icon': False
                }
        cur = db.cursor()
        result = cur.execute(QUERY_BITICON_BY_USER, {'user':int(user_id)}).fetchall()
        if result:
            (result, col_names) = rowify(result, cur.description)
            user_data = result[0]

        cur.close()
        return encoder.encode(user_data)

class ChooseBitView(MethodView):
    """Choose a bit"""
    decorators = [user_not_banned]

    def get(self):
        "Show a batch of available bit icon names"

        save_cookie = False
        offset_seconds = current_app.secure_cookie.get(u'ot')
        if not offset_seconds:
            save_cookie = True
            offset_seconds = str(randint(1, 900))
        offset_time = '{} seconds'.format(int(offset_seconds))

        limit = request.args.get('limit')
        if not limit:
            limit = 7
        try:
            limit = int(limit)
        except ValueError:
            limit = 7
        if limit not in (49, 7):
            limit = 7


        cur = db.cursor()
        # List of bit icon names that are available
        result = cur.execute(fetch_query_string('select_random_bit_batch.sql'), {'offset_time': offset_time, 'limit': limit}).fetchall()
        (result, col_names) = rowify(result, cur.description)
        bits = [x['icon'] for x in result]


        response = make_response(encoder.encode({'data':bits}), 200)
        if save_cookie:
            current_app.secure_cookie.set(u'ot', str(offset_seconds), response, expires_days=1)

        cur.close()
        return response

class ClaimBitView(MethodView):
    """Claim a bit and register new user"""
    decorators = [user_not_banned]

    def post(self):
        """If the bit icon is available; claim it for the user."""
        icon = request.args.get('icon')
        if not icon:
            abort(400)

        # Prevent creating a new user if no support for cookies. Player should
        # have 'ot' already set by viewing the page.
        uses_cookies = current_app.secure_cookie.get(u'ot')
        if not uses_cookies:
            abort(400)

        cur = db.cursor()

        # Check if bit icon is available
        result = cur.execute(fetch_query_string('select_available_bit_icon.sql'), {'icon': icon}).fetchone()
        if not result:
            cur.close()
            abort(400)

        response = make_response('', 200)
        user = current_app.secure_cookie.get(u'user')
        if not user:
            user = user_id_from_ip(request.headers.get('X-Real-IP'))
            if user == None:
                abort(400)
            user = int(user)

        else:
            user = int(user)


        # Unclaim any bit icon that the player already has
        cur.execute(fetch_query_string('unclaim_bit_icon.sql'), {'user': user})

        # Claim the bit icon
        cur.execute(fetch_query_string('update_bit_icon_user.sql'), {'user': user, 'icon':icon})

        cur.close()
        db.commit()
        return response


class ClaimUserView(MethodView):
    """Claim a bit and register new user"""
    decorators = [user_not_banned]

    def register_new_user(self, user_id):
        """Update initial ip tracked user to now be cookie tracked with a password."""
        cur = db.cursor()

        login = generate_user_login()
        (p_string, password) = generate_password()

        query = """
        update User set
        password = :password,
        m_date = datetime('now'),
        cookie_expires = strftime('%Y-%m-%d', 'now', '+14 days')
        where ip = :ip and id = :id and password isnull;
        """
        cur.execute(query, {'id': user_id, 'password': password, 'ip': request.headers.get('X-Real-IP')})
        # Other players on the same network that are tracked by shareduser
        # cookie will have it updated to a new value.
        db.commit()
        cur.close()

    def post(self):
        """Update shareduser to user"""

        # Prevent creating a new user if no support for cookies. Player should
        # have 'ot' already set by viewing the page.
        uses_cookies = current_app.secure_cookie.get(u'ot')
        if not uses_cookies:
            abort(400)

        cur = db.cursor()

        response = make_response('', 200)

        user = user_id_from_ip(request.headers.get('X-Real-IP'))
        if user == None:
            abort(400)
        user = int(user)

        # Only set new user if enough dots
        result = cur.execute("select points from User where id = :id and points >= :startpoints + :cost;", {'id': user, 'cost': POINT_COST_FOR_CHANGING_BIT, 'startpoints': NEW_USER_STARTING_POINTS}).fetchone()
        if result:
            self.register_new_user(user)
            # Save as a cookie
            current_app.secure_cookie.set(u'user', str(user), response, expires_days=365)
            # Remove shareduser
            expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
            current_app.secure_cookie.set(u'shareduser', "", response, expires=expires)

            cur.execute("update User set points = points - :cost where id = :id;", {'id': user, 'cost': POINT_COST_FOR_CHANGING_BIT})

        cur.close()
        db.commit()
        return response
