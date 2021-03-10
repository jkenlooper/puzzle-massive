from __future__ import print_function
from builtins import bytes
import os
import re
import time
import uuid
import threading
import requests
import subprocess
import tempfile

import sqlite3
from PIL import Image
from flask import current_app, redirect, request, make_response, abort, json
from flask.views import MethodView
from werkzeug.utils import secure_filename, escape
from werkzeug.urls import url_fix

from api.app import redis_connection, db, make_app
from api.database import (
    rowify,
    fetch_query_string,
    read_query_file,
    generate_new_puzzle_id,
)
from api.constants import (
    COMPLETED,
    NEEDS_MODERATION,
    PRIVATE,
    PUBLIC,
    CLASSIC,
    QUEUE_NEW,
)
from api.user import user_id_from_ip, user_not_banned, ANONYMOUS_USER_ID
from api.tools import check_bg_color

# Not allowing anything other then jpg to protect against potential picture bombs.
ALLOWED_EXTENSIONS = set(["jpg", "jpeg"])


def submit_puzzle(
    pieces,
    bg_color,
    user,
    permission,
    description,
    link,
    upload_file,
    secret_message="",
    features=set(),
):
    """
    Submit a puzzle to be reviewed.  Generates the puzzle_id and original.jpg.
    """
    unsplash_image_thread = None

    puzzle_id = None
    cur = db.cursor()

    unsplash_match = re.search(r"^(http://|https://)?unsplash.com/photos/([^/]+)", link)
    if link and unsplash_match:
        if not current_app.config.get("UNSPLASH_APPLICATION_ID"):
            cur.close()
            abort(400)

        filename = unsplash_match.group(2)
        u_id = uuid.uuid4().hex[:20]
        puzzle_id = f"unsplash-mxyz-{u_id}"

        # Create puzzle dir
        puzzle_dir = os.path.join(current_app.config.get("PUZZLE_RESOURCES"), puzzle_id)
        os.mkdir(puzzle_dir)

        # Download the unsplash image
        unsplash_image_thread = UnsplashPuzzleThread(
            puzzle_id,
            filename,
            description,
            current_app.config_file,
            current_app.config.get("SECURE_COOKIE_SECRET"),
        )
    else:
        if not upload_file:
            cur.close()
            abort(400)
        filename = secure_filename(upload_file.filename)
        filename = filename.lower()

        # Check the filename to see if the extension is allowed
        if os.path.splitext(filename)[1][1:].lower() not in ALLOWED_EXTENSIONS:
            cur.close()
            abort(400)

        puzzle_id = generate_new_puzzle_id(filename)

        # Create puzzle dir
        puzzle_dir = os.path.join(current_app.config.get("PUZZLE_RESOURCES"), puzzle_id)
        os.mkdir(puzzle_dir)

        # Convert the uploaded file to jpg
        with tempfile.NamedTemporaryFile() as temp_upload_file:
            upload_file.save(temp_upload_file)

            # verify the image file format
            identify_format = subprocess.check_output(
                ["identify", "-format", "%m", temp_upload_file.name], encoding="utf-8"
            )
            identify_format = identify_format.lower()
            current_app.logger.debug(
                f"identify_format {identify_format} in {ALLOWED_EXTENSIONS}"
            )
            if identify_format not in ALLOWED_EXTENSIONS:
                os.rmdir(puzzle_dir)
                cur.close()
                abort(400)

            # Abort if imagemagick fails converting the image to jpg
            try:
                subprocess.check_call(
                    [
                        "convert",
                        temp_upload_file.name,
                        "-quality",
                        "85%",
                        "-format",
                        "jpg",
                        os.path.join(puzzle_dir, "original.jpg"),
                    ]
                )
            except subprocess.CalledProcessError:
                os.rmdir(puzzle_dir)
                cur.close()
                abort(400)

        # The preview_full image is only created in the pieceRender process.

    d = {
        "puzzle_id": puzzle_id,
        "pieces": pieces,
        "name": filename,
        "link": link,
        "description": description,
        "bg_color": bg_color,
        "owner": user,
        "queue": QUEUE_NEW,
        "status": NEEDS_MODERATION,
        "permission": permission,
    }
    cur.execute(
        fetch_query_string("insert_puzzle.sql"),
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

    cur.execute(
        fetch_query_string("add-puzzle-file.sql"),
        {
            "puzzle": puzzle,
            "name": "original",
            "url": "/resources/{0}/original.jpg".format(
                puzzle_id
            ),  # Not a public file (only on admin page)
        },
    )

    # The preview_full image is created in the unsplash_image_thread.
    if not unsplash_match:
        slip = uuid.uuid4().hex[:4]
        preview_full_slip = f"preview_full.{slip}.jpg"
        cur.execute(
            fetch_query_string("add-puzzle-file.sql"),
            {
                "puzzle": puzzle,
                "name": "preview_full",
                "url": f"/resources/{puzzle_id}/{preview_full_slip}",
            },
        )

    classic_variant = cur.execute(
        fetch_query_string("select-puzzle-variant-id-for-slug.sql"), {"slug": CLASSIC}
    ).fetchone()[0]
    cur.execute(
        fetch_query_string("insert-puzzle-instance.sql"),
        {"original": puzzle, "instance": puzzle, "variant": classic_variant},
    )

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

    if unsplash_image_thread:
        # Go download the unsplash image and update the db
        unsplash_image_thread.start()

    return puzzle_id


class PuzzleUploadView(MethodView):
    """
    Handle uploaded puzzle images
    """

    decorators = [user_not_banned]

    def post(self):
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))
            args["features"] = set(request.form.getlist("features"))

        # Only allow valid contributor
        if args.get("contributor", None) != current_app.config.get(
            "NEW_PUZZLE_CONTRIB"
        ):
            abort(403)

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
        cur = db.cursor()
        results = cur.execute(
            fetch_query_string("select-user-details-by-id.sql"),
            {"id": user},
        ).fetchone()
        if not result:
            # Safe guard against when the user is not in the database. Usually
            # happens in development environments when switching and dropping
            # databases happens often.
            user = ANONYMOUS_USER_ID
        cur.close()

        permission = int(args.get("permission", PUBLIC))
        if permission not in (PUBLIC, PRIVATE):
            permission = PUBLIC

        description = escape(args.get("description", ""))[:1000]

        # Check secret_message
        secret_message = escape(args.get("secret_message", ""))[:1000]

        # Check link and validate
        link = url_fix(args.get("link", ""))[:1000]

        upload_file = request.files.get("upload_file", None)

        features = set(args.get("features", []))

        puzzle_id = submit_puzzle(
            pieces,
            bg_color,
            user,
            permission,
            description,
            link,
            upload_file,
            secret_message=secret_message,
            features=features,
        )

        return redirect("/chill/site/front/{0}/".format(puzzle_id), code=303)


class AdminPuzzlePromoteSuggestedView(MethodView):
    """
    Handle promoting a suggested puzzle to be in needs moderation status.
    """

    def post(self):
        "Route is protected by basic auth in nginx"
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))
            args["features"] = set(request.form.getlist("features"))

        puzzle_id = args.get("puzzle_id")
        if not puzzle_id:
            abort(400)

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

        # All puzzles are public by default, but allow the admin to set
        # permission to PRIVATE.
        permission = int(args.get("permission", PUBLIC))
        if permission not in (PUBLIC, PRIVATE):
            permission = PUBLIC

        description = escape(args.get("description", ""))[:1000]

        # Check secret_message
        secret_message = escape(args.get("secret_message", ""))[:1000]

        # Check link and validate
        link = url_fix(args.get("link", ""))[:1000]

        upload_file = request.files.get("upload_file", None)

        # Get the owner of the suggested puzzle
        cur = db.cursor()
        result = cur.execute(
            fetch_query_string("_select-owner-for-suggested-puzzle.sql"),
            {"puzzle_id": puzzle_id},
        ).fetchone()
        if not result:
            cur.close()
            abort(400)
        owner = int(result[0])
        if owner == 0:
            # Safe guard against when the user is not in the database. Usually
            # happens in development environments when switching and dropping
            # databases happens often.
            owner = ANONYMOUS_USER_ID

        features = args.get("features")

        new_puzzle_id = submit_puzzle(
            pieces,
            bg_color,
            owner,
            permission,
            description,
            link,
            upload_file,
            secret_message=secret_message,
            features=features,
        )

        # Update the status of this suggested puzzle to be the suggested done
        # status
        cur.execute(
            fetch_query_string("_update-suggested-puzzle-to-done-status.sql"),
            {"puzzle_id": puzzle_id},
        )
        db.commit()
        cur.close()

        return redirect("/chill/site/admin/puzzle/suggested/", code=303)


class AdminPuzzleUnsplashBatchView(MethodView):
    ""

    def post(self):
        "Route is protected by basic auth in nginx"
        args = {}
        batch = []

        user = int(
            current_app.secure_cookie.get("user")
            or user_id_from_ip(request.headers.get("X-Real-IP"))
        )
        cur = db.cursor()
        results = cur.execute(
            fetch_query_string("select-user-details-by-id.sql"),
            {"id": user},
        ).fetchone()
        if not result:
            # Safe guard against when the user is not in the database. Usually
            # happens in development environments when switching and dropping
            # databases happens often.
            user = ANONYMOUS_USER_ID
        cur.close()

        if request.form:
            args.update(request.form.to_dict(flat=True))
            labels = ["unlisted", "hidden_preview", "link", "bg_color", "pieces"]
            batch = list(
                map(
                    lambda x: dict(zip(labels, x)),
                    list(zip(*list(map(request.form.getlist, labels)))),
                )
            )

        for item in batch:
            try:
                pieces = int(
                    item.get("pieces", current_app.config["MINIMUM_PIECE_COUNT"])
                )
            except ValueError as err:
                abort(400)
            if (
                not current_app.config["MINIMUM_PIECE_COUNT"]
                <= pieces
                <= current_app.config["MAXIMUM_PIECE_COUNT"]
            ):
                abort(400)
            bg_color = check_bg_color(item.get("bg_color", "#808080")[:50])
            permission = PUBLIC if item.get("unlisted", "false") == "false" else PRIVATE
            description = ""
            link = url_fix(item.get("link", ""))[:1000]
            secret_message = escape(item.get("secret_message", ""))[:1000]
            features = set()
            if item.get("hidden_preview", "false") != "false":
                features.add("hidden-preview")

            puzzle_id = submit_puzzle(
                pieces,
                bg_color,
                user,
                permission,
                description,
                link,
                upload_file=None,
                secret_message=secret_message,
                features=features,
            )

        return redirect("/chill/site/player-puzzle-list/", code=303)


class UnsplashPuzzleThread(threading.Thread):
    def __init__(self, puzzle_id, photo, description, config_file, cookie_secret):
        threading.Thread.__init__(self)
        self.puzzle_id = puzzle_id
        self.photo = photo
        self.description = description

        self.app = make_app(config=config_file, cookie_secret=cookie_secret)

        self.application_id = (self.app.config.get("UNSPLASH_APPLICATION_ID"),)
        self.puzzle_resources = self.app.config.get("PUZZLE_RESOURCES")
        self.application_name = self.app.config.get("UNSPLASH_APPLICATION_NAME")

    def run(self):
        with self.app.app_context():
            r = requests.get(
                "https://api.unsplash.com/photos/%s" % self.photo,
                params={
                    "client_id": self.application_id,
                    "w": 384,
                    "h": 384,
                    "fit": "max",
                },
                headers={"Accept-Version": "v1"},
            )
            data = r.json()

            self.add_puzzle(data)

    def add_puzzle(self, data):
        cur = db.cursor()

        # Don't use unsplash description if puzzle already has one
        description = (
            self.description
            if self.description
            else escape(data.get("description", None))
        )

        puzzle_dir = os.path.join(self.puzzle_resources, self.puzzle_id)
        filename = os.path.join(puzzle_dir, "original.jpg")
        f = open(filename, "w+b")

        links = data.get("links")
        if not links:
            raise Exception("Unsplash returned no links")
        download = links.get("download")
        if not download:
            raise Exception("Unsplash returned no download")
        r = requests.get(download)
        f.write(r.content)
        f.close()

        r = requests.patch(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                HOSTAPI=self.app.config["HOSTAPI"],
                PORTAPI=self.app.config["PORTAPI"],
                puzzle_id=self.puzzle_id,
            ),
            json={"link": "", "description": description},
        )
        if r.status_code != 200:
            raise Exception(
                "Puzzle details api error when setting link and description on unsplash photo upload {}".format(
                    self.puzzle_id
                )
            )

        puzzle = rowify(
            cur.execute(
                read_query_file("select_puzzle_id_by_puzzle_id.sql"),
                {"puzzle_id": self.puzzle_id},
            ).fetchall(),
            cur.description,
        )[0][0]["puzzle"]

        # Set preview full url and fallback to small
        preview_full_url = data.get("urls", {}).get(
            "custom", data.get("urls", {}).get("small")
        )
        # Use the max version to keep the image ratio and not crop it.
        preview_full_url = re.sub("fit=crop", "fit=max", preview_full_url)

        # Not using url_fix on the user.links.html since it garbles the '@'.
        r = requests.post(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                HOSTAPI=self.app.config["HOSTAPI"],
                PORTAPI=self.app.config["PORTAPI"],
                puzzle_id=self.puzzle_id,
                file_name="preview_full",
            ),
            json={
                "attribution": {
                    "title": "Photo",
                    "author_link": "{user_link}?utm_source={application_name}&utm_medium=referral".format(
                        user_link=data.get("user").get("links").get("html"),
                        application_name=self.application_name,
                    ),
                    "author_name": data.get("user").get("name"),
                    "source": "{photo_link}?utm_source={application_name}&utm_medium=referral".format(
                        photo_link=data.get("links").get("html"),
                        application_name=self.application_name,
                    ),
                    "license_name": "unsplash",
                },
                "url": preview_full_url,
            },
        )
        if r.status_code != 200:
            raise Exception(
                "Puzzle file api error when setting attribution and url for unsplash preview_full {}".format(
                    self.puzzle_id
                )
            )

        cur.close()
