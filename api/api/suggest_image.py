from __future__ import absolute_import
import uuid

import sqlite3
from flask import current_app, redirect, request, abort
from flask.views import MethodView
from markupsafe import escape
from werkzeug.urls import url_fix

from api.app import db
from api.database import (
    rowify,
    fetch_query_string,
)
from api.tools import check_bg_color
from api.constants import SUGGESTED, PUBLIC, PRIVATE
from api.user import user_id_from_ip
from api.notify import send_message
from .user import user_not_banned


class SuggestImageView(MethodView):
    """
    Handle suggest image form uploads.
    Only the first 100 chars of the link and description are sent in the email message.
    """

    decorators = [user_not_banned]

    def post(self):
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))
            args["features"] = set(request.form.getlist("features"))

        # Check pieces arg
        try:
            pieces = int(args.get("pieces", current_app.config["MINIMUM_PIECE_COUNT"]))
        except ValueError as err:
            abort(400)
        if (
            not current_app.config["MINIMUM_PIECE_COUNT"]
            <= pieces
            <= current_app.config["MAXIMUM_PIECE_COUNT"]
        ):
            abort(400)

        bg_color = check_bg_color(args.get("bg_color", "#808080")[:50])

        user = int(
            current_app.secure_cookie.get("user")
            or user_id_from_ip(request.headers.get("X-Real-IP"))
        )

        permission = int(args.get("permission", PUBLIC))
        if permission not in (PUBLIC, PRIVATE):
            permission = PUBLIC

        description = escape(args.get("description", "").strip())[:1000]

        # Check secret_message
        secret_message = escape(args.get("secret_message", ""))[:1000]

        # Check link and validate
        link = url_fix(args.get("link", "").strip())[:100]

        if not link and not description:
            abort(400)

        puzzle_id = uuid.uuid1().hex

        features = set(args.get("features", []))

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

        puzzle = rowify(
            cur.execute(
                fetch_query_string("select_puzzle_id_by_puzzle_id.sql"),
                {"puzzle_id": puzzle_id},
            ).fetchall(),
            cur.description,
        )[0][0]
        puzzle = puzzle["puzzle"]

        result = cur.execute(
            fetch_query_string("select-puzzle-features-enabled.sql"), {"enabled": 1}
        ).fetchall()
        if result:
            (puzzle_features, _) = rowify(result, cur.description)
            # Add puzzle features
            for puzzle_feature in puzzle_features:
                if (
                    puzzle_feature["slug"] == "hidden-preview"
                    and "hidden-preview" in features
                ):
                    cur.execute(
                        fetch_query_string(
                            "add-puzzle-feature-to-puzzle-by-id--hidden-preview.sql"
                        ),
                        {"puzzle": puzzle, "puzzle_feature": puzzle_feature["id"]},
                    )
                elif (
                    puzzle_feature["slug"] == "secret-message"
                    and "secret-message" in features
                ):
                    cur.execute(
                        fetch_query_string(
                            "add-puzzle-feature-to-puzzle-by-id--secret-message.sql"
                        ),
                        {
                            "puzzle": puzzle,
                            "puzzle_feature": puzzle_feature["id"],
                            "message": secret_message,
                        },
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
