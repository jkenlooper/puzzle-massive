import os
import re

import requests
from flask import current_app
from werkzeug.utils import escape


def add_photo_to_puzzle(puzzle_id, photo, description):
    ""

    with current_app.app_context():
        application_id = (current_app.config.get("UNSPLASH_APPLICATION_ID"),)
        puzzle_resources = current_app.config.get("PUZZLE_RESOURCES")
        application_name = current_app.config.get("UNSPLASH_APPLICATION_NAME")

        r = requests.get(
            f"https://api.unsplash.com/photos/{photo}",
            params={
                "client_id": application_id,
                "w": 384,
                "h": 384,
                "fit": "max",
            },
            headers={"Accept-Version": "v1"},
        )
        data = r.json()

        # Don't use unsplash description if puzzle already has one
        description = (
            description if description else escape(data.get("description", None))
        )

        puzzle_dir = os.path.join(puzzle_resources, puzzle_id)
        filename = os.path.join(puzzle_dir, "original.jpg")
        links = data.get("links")
        if not links:
            raise Exception("Unsplash returned no links")
        download = links.get("download")
        if not download:
            raise Exception("Unsplash returned no download")
        r = requests.get(download)
        with open(filename, "w+b") as f:
            f.write(r.content)

        r = requests.patch(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                HOSTAPI=current_app.config["HOSTAPI"],
                PORTAPI=current_app.config["PORTAPI"],
                puzzle_id=puzzle_id,
            ),
            json={"link": "", "description": description},
        )
        if r.status_code != 200:
            raise Exception(
                "Puzzle details api error when setting link and description on unsplash photo upload {}".format(
                    puzzle_id
                )
            )

        # Set preview full url and fallback to small
        preview_full_url = data.get("urls", {}).get(
            "custom", data.get("urls", {}).get("small")
        )
        # Use the max version to keep the image ratio and not crop it.
        preview_full_url = re.sub("fit=crop", "fit=max", preview_full_url)

        # Not using url_fix on the user.links.html since it garbles the '@'.
        r = requests.post(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                HOSTAPI=current_app.config["HOSTAPI"],
                PORTAPI=current_app.config["PORTAPI"],
                puzzle_id=puzzle_id,
                file_name="preview_full",
            ),
            json={
                "attribution": {
                    "title": "Photo",
                    "author_link": "{user_link}?utm_source={application_name}&utm_medium=referral".format(
                        user_link=data.get("user").get("links").get("html"),
                        application_name=application_name,
                    ),
                    "author_name": data.get("user").get("name"),
                    "source": "{photo_link}?utm_source={application_name}&utm_medium=referral".format(
                        photo_link=data.get("links").get("html"),
                        application_name=application_name,
                    ),
                    "license_name": "unsplash",
                },
                "url": preview_full_url,
            },
        )
        if r.status_code != 200:
            raise Exception(
                "Puzzle file api error when setting attribution and url for unsplash preview_full {}".format(
                    puzzle_id
                )
            )
