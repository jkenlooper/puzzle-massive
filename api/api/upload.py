from __future__ import print_function
from builtins import bytes
import os
import re
import uuid
import subprocess
import tempfile

from PIL import Image
from flask import current_app, redirect, request, abort
from flask.views import MethodView
from werkzeug.utils import secure_filename, escape
from werkzeug.urls import url_fix

from api.app import db
from api.database import (
    rowify,
    fetch_query_string,
    generate_new_puzzle_id,
)
from api.constants import (
    NEEDS_MODERATION,
    IN_RENDER_QUEUE,
    REBUILD,
    PRIVATE,
    PUBLIC,
    CLASSIC,
    QUEUE_NEW,
)
from api.user import user_id_from_ip, user_not_banned, ANONYMOUS_USER_ID
from api.tools import check_bg_color
from api.puzzle_resource import PuzzleResource

# Not allowing anything other then jpg to protect against potential picture bombs.
ALLOWED_EXTENSIONS = set(["jpg", "jpeg"])

unsplash_url_regex = r"^(http://|https://)?unsplash.com/photos/([^/]+)"


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

    puzzle_id = None
    filename = ""
    original_slip = uuid.uuid4().hex[:10]
    cur = db.cursor()

    unsplash_match = re.search(unsplash_url_regex, link)
    is_unsplash_link = True if link and unsplash_match else False
    if is_unsplash_link:
        if not current_app.config.get("UNSPLASH_APPLICATION_ID"):
            cur.close()
            abort(400)

        filename = unsplash_match.group(2)
        u_id = uuid.uuid4().hex[:20]
        puzzle_id = f"unsplash-mxyz-{u_id}"

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

    pr = PuzzleResource(puzzle_id, current_app.config)
    puzzle_dir = pr.yank()

    if not is_unsplash_link:
        # Convert the uploaded file to jpg
        with tempfile.NamedTemporaryFile() as temp_upload_file:
            upload_file.save(temp_upload_file)

            # verify the image file format
            identify_format = subprocess.check_output(
                ["identify", "-format", "%m", temp_upload_file.name], encoding="utf-8"
            )
            identify_format = identify_format.lower()
            if identify_format not in ALLOWED_EXTENSIONS:
                pr.delete()
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
                        os.path.join(puzzle_dir, f"original.{original_slip}.jpg"),
                    ]
                )
            except subprocess.CalledProcessError:
                pr.delete()
                cur.close()
                abort(400)

    d = {
        "puzzle_id": puzzle_id,
        "pieces": pieces,
        "name": filename,
        "link": link,
        "description": description,
        "bg_color": bg_color,
        "owner": user,
        "queue": QUEUE_NEW,
        "status": NEEDS_MODERATION
        if not current_app.config["AUTO_APPROVE_PUZZLES"]
        else IN_RENDER_QUEUE,
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
            "url": f"/resources/{puzzle_id}/original.{original_slip}.jpg"
        },
    )

    if not is_unsplash_link:
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
        im = Image.open(os.path.join(puzzle_dir, f"original.{original_slip}.jpg")).copy()
        im.thumbnail(size=(384, 384))
        im.save(os.path.join(puzzle_dir, preview_full_slip))
        im.close()

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

    if is_unsplash_link:
        original_filename = f"original.{original_slip}.jpg"
        # TODO: push to artist queue to enqueue_in(timedelta(seconds=10))
        # https://python-rq.org/docs/scheduling/
        # Go download the unsplash image and update the db
        job = current_app.unsplashqueue.enqueue(
            "api.jobs.unsplash_image.add_photo_to_puzzle",
            puzzle_id,
            filename,
            description,
            original_filename,
            result_ttl=0,
            job_timeout="24h",
        )

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
        result = cur.execute(
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

        # TODO AUTO_APPROVE_PUZZLES only works for non Unsplash photos at the moment.
        if current_app.config["AUTO_APPROVE_PUZZLES"] and not re.search(
            unsplash_url_regex, link
        ):
            cur = db.cursor()
            puzzles = rowify(
                cur.execute(
                    fetch_query_string("select-puzzles-in-render-queue.sql"),
                    {"IN_RENDER_QUEUE": IN_RENDER_QUEUE, "REBUILD": REBUILD},
                ).fetchall(),
                cur.description,
            )[0]
            cur.close()
            print("found {0} puzzles to render or rebuild".format(len(puzzles)))

            # push each puzzle to artist job queue
            for puzzle in puzzles:
                job = current_app.createqueue.enqueue(
                    "api.jobs.pieceRenderer.render",
                    [puzzle],
                    result_ttl=0,
                    job_timeout="24h",
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
        result = cur.execute(
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
