import os
import re
from datetime import timedelta

import requests
from flask import current_app
from werkzeug.utils import escape

from api.app import redis_connection

# When not in demo mode it is 1000. Get actual value from the header X-Ratelimit-Limit.
UNSPLASH_RATELIMIT_LIMIT_DEMO = 50


def add_photo_to_puzzle(puzzle_id, photo, description):
    ""

    with current_app.app_context():
        application_id = (current_app.config.get("UNSPLASH_APPLICATION_ID"),)
        puzzle_resources = current_app.config.get("PUZZLE_RESOURCES")
        application_name = current_app.config.get("UNSPLASH_APPLICATION_NAME")

        # Prevent going past the Unsplash rate limit by storing the current
        # remaining in the unsplash:rlr key.
        unsplash_rate_limit_remaining = int(
            redis_connection.get("unsplash:rlr") or UNSPLASH_RATELIMIT_LIMIT_DEMO
        )
        # Playing it safe by not getting too close to the limit.
        if unsplash_rate_limit_remaining < int(UNSPLASH_RATELIMIT_LIMIT_DEMO / 3):
            current_app.logger.info(
                f"Reaching the Unsplash rate limit. Requeueing puzzle {puzzle_id}"
            )
            job = current_app.unsplashqueue.enqueue_in(
                timedelta(hours=1, minutes=10, seconds=42),
                "api.jobs.unsplash_image.add_photo_to_puzzle",
                puzzle_id,
                photo,
                description,
                result_ttl=0,
                job_timeout="24h",
            )
            return

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

        current_app.logger.debug(r.headers)
        unsplash_rate_limit_remaining = int(
            r.headers.get("X-Ratelimit-Remaining", UNSPLASH_RATELIMIT_LIMIT_DEMO)
        )
        # Unsplash rate limit is by the hour.
        redis_connection.setex(
            "unsplash:rlr", timedelta(hours=1), unsplash_rate_limit_remaining
        )

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
