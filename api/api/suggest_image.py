import re
import uuid

import sqlite3
from flask import current_app, redirect, request, abort
from flask.views import MethodView
from werkzeug.utils import escape
from werkzeug.urls import url_fix

from api.app import db
from api.database import rowify
from api.constants import SUGGESTED
from api.user import user_id_from_ip

#permissions
PUBLIC   = 0  # obvious...

class SuggestImageView(MethodView):
    """
    Handle suggest image form uploads
    """
    def post(self):
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # Check pieces arg
        pieces = args.get('pieces', 100)
        if pieces < 2:
            abort(400)

        # Check bg_color
        color_regex = re.compile('.*?#?([a-f0-9]{6}|[a-f0-9]{3}).*?', re.IGNORECASE)
        bg_color = args.get('bg_color', '#808080')[:50]
        color_match = color_regex.match(bg_color)
        if (color_match):
            bg_color = "#{0}".format(color_match.group(1))
        else:
            bg_color = "#808080"

        # Verify user is logged in
        user = current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP'))
        if user == None:
            abort(403)

        # All puzzles are public
        permission = PUBLIC
        #permission = int(args.get('permission', PUBLIC))
        #if permission != PUBLIC:
        #    permission = PUBLIC

        description = escape(args.get('description', ''))

        # Check link and validate
        link = url_fix(args.get('link', ''))

        puzzle_id = uuid.uuid1().hex

        cur = db.cursor()
        d = {'puzzle_id':puzzle_id,
            'pieces':pieces,
            'link':link,
            'description':description,
            'bg_color':bg_color,
            'owner':user,
            'status': SUGGESTED,
            'permission':permission}
        cur.execute("""insert into Puzzle (
        puzzle_id,
        pieces,
        link,
        description,
        bg_color,
        owner,
        status,
        permission) values
        (:puzzle_id,
        :pieces,
        :link,
        :description,
        :bg_color,
        :owner,
        :status,
        :permission);
        """, d)
        db.commit()

        # TODO: send a notification email

        # Redirect to a thank you page (not revealing the puzzle_id)
        return redirect('/chill/site/suggested-puzzle-thank-you/', code=303)

