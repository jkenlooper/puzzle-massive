from __future__ import absolute_import
import uuid

import sqlite3
from flask import current_app, redirect, request, abort
from flask.views import MethodView
from werkzeug.utils import escape
from werkzeug.urls import url_fix

from api.app import db
from api.database import rowify
from api.tools import check_bg_color
from api.constants import SUGGESTED, PUBLIC
from api.user import user_id_from_ip
from api.notify import send_message
from .user import user_not_banned


class SuggestImageView(MethodView):
    """
    Handle suggest image form uploads
    """

    decorators = [user_not_banned]

    def post(self):
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # Check pieces arg
        try:
            pieces = int(args.get("pieces", current_app.config["MINIMUM_PIECE_COUNT"]))
        except ValueError as err:
            abort(400)
        if pieces < current_app.config["MINIMUM_PIECE_COUNT"]:
            abort(400)

        bg_color = check_bg_color(args.get("bg_color", "#808080")[:50])

        user = int(
            current_app.secure_cookie.get(u"user")
            or user_id_from_ip(request.headers.get("X-Real-IP"))
        )

        # All puzzles are public
        permission = PUBLIC
        # permission = int(args.get('permission', PUBLIC))
        # if permission != PUBLIC:
        #    permission = PUBLIC

        description = escape(args.get("description", ""))[:1000]

        # Check link and validate
        link = url_fix(args.get("link", ""))[:1000]

        puzzle_id = uuid.uuid1().hex

        cur = db.cursor()
        d = {
            "puzzle_id": puzzle_id,
            "pieces": pieces,
            "link": link,
            "description": description,
            "bg_color": bg_color,
            "owner": user,
            "status": SUGGESTED,
            "permission": permission,
        }
        cur.execute(
            """insert into Puzzle (
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
        """,
            d,
        )
        db.commit()
        cur.close()

        # Send a notification email (silent fail if not configured)
        message = """
http://{DOMAIN_NAME}/chill/site/admin/puzzle/suggested/{puzzle_id}/

pieces: {pieces}
bg_color: {bg_color}
owner: {owner}

link: {link}
description: {description}
        """.format(
            DOMAIN_NAME=current_app.config.get("DOMAIN_NAME"), **d
        )
        current_app.logger.debug(message)
        if not current_app.config.get("DEBUG", True):
            try:
                send_message(
                    current_app.config.get("EMAIL_MODERATOR"),
                    "Suggested Image",
                    message,
                    current_app.config,
                )
            except Exception as err:
                current_app.logger.warning(
                    "Failed to send notification message for suggested image. email: {email}\n {message}\n error: {err}".format(
                        err=err,
                        email=current_app.config.get("EMAIL_MODERATOR"),
                        message=message,
                    )
                )
                pass

        # Redirect to a thank you page (not revealing the puzzle_id)
        return redirect("/chill/site/suggested-puzzle-thank-you/", code=303)
