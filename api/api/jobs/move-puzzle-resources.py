#!/usr/bin/env python
"""move-puzzle-resources.py

Usage: move-puzzle-resources.py [--destructive]
       move-puzzle-resources.py --help

Options:
  -h --help         Show this screen.
  --destructive     Remove puzzle files after moving to new location
"""

import os.path
from time import sleep
import re

from docopt import docopt
from flask import current_app
import requests

from api.app import make_app
from api.tools import loadConfig
from api.puzzle_resource import PuzzleResource


def move_all_to_s3(is_destructive=False):
    ""

    HOSTAPI = current_app.config["HOSTAPI"]
    PORTAPI = current_app.config["PORTAPI"]
    CDN_BASE_URL = current_app.config["CDN_BASE_URL"]

    r = requests.get(
        f"http://{HOSTAPI}:{PORTAPI}/internal/puzzle-rendered-resources-list/?url_match=/resources/%"
    )
    if r.status_code != 200:
        raise Exception(f"Internal puzzle-rendered-resources-list api error. {r}")

    response = r.json()
    print(f"Found {len(response.get('puzzle_files'))} puzzle files to move to s3.")
    if is_destructive:
        print(
            f"The files in {current_app.config['PUZZLE_RESOURCES']} will be removed after they are uploaded to s3."
        )
    confirm = input("Continue? y/n ")
    if confirm.lower() != "y":
        print("Cancelling move to s3.")
        return

    for puzzle_file in response.get("puzzle_files"):
        current_app.logger.info("Moving {puzzle_id} {name} {url}".format(**puzzle_file))
        puzzle_id = puzzle_file["puzzle_id"]
        # Also strip out any query params that may be part of the url.
        file_path = re.sub(r"\?.*$", "", puzzle_file["url"][len(f"/resources/{puzzle_id}/") :])
        local_pr = PuzzleResource(puzzle_id, current_app.config, is_local_resource=True)
        s3_pr = PuzzleResource(puzzle_id, current_app.config, is_local_resource=False)

        my_yanked_file_path = local_pr.yank_file(file_path)

        try:
            s3_pr.put_file(
                my_yanked_file_path,
                dirs=os.path.dirname(my_yanked_file_path[len(local_pr.target_dir) + 1 :]),
            )
        except FileNotFoundError:
            current_app.logger.warn(f"Skipping missing file: {my_yanked_file_path}")
            continue

        r = requests.patch(
            f"http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/files/{puzzle_file['name']}/",
            json={
                "url": f"{CDN_BASE_URL}/resources/{puzzle_id}/{my_yanked_file_path[len(local_pr.target_dir)+1:]}",
            },
        )
        if r.status_code != 200:
            raise Exception(f"move_all_to_s3 error.  Request failed. {r}")
        if is_destructive:
            local_pr.purge_file(file_path)

        # Rate limiting to avoid going over the s3 request limits.
        sleep(0.1)


def move_all_from_s3(is_destructive=False):
    ""
    HOSTAPI = current_app.config["HOSTAPI"]
    PORTAPI = current_app.config["PORTAPI"]
    CDN_BASE_URL = current_app.config["CDN_BASE_URL"]

    # The remote resource URL should be the same configured CDN_BASE_URL as when
    # it was initially uploaded.
    r = requests.get(
        f"http://{HOSTAPI}:{PORTAPI}/internal/puzzle-rendered-resources-list/?url_match={CDN_BASE_URL}/resources/%"
    )
    if r.status_code != 200:
        raise Exception(f"Internal puzzle-rendered-resources-list api error. {r}")
    response = r.json()
    print(f"Found {len(response.get('puzzle_files'))} puzzle files to move from s3.")
    if is_destructive:
        print(
            f"The files at {CDN_BASE_URL}/resources/ will be removed after they are downloaded to {current_app.config['PUZZLE_RESOURCES']}/"
        )
    confirm = input("Continue? y/n ")
    if confirm.lower() != "y":
        print("Cancelling move from s3.")
        return

    for puzzle_file in response.get("puzzle_files"):
        current_app.logger.info("Moving {puzzle_id} {name} {url}".format(**puzzle_file))
        puzzle_id = puzzle_file["puzzle_id"]
        file_path = puzzle_file["url"][len(f"{CDN_BASE_URL}/resources/{puzzle_id}/") :]
        s3_pr = PuzzleResource(puzzle_id, current_app.config, is_local_resource=False)
        local_pr = PuzzleResource(puzzle_id, current_app.config, is_local_resource=True)

        my_yanked_file_path = s3_pr.yank_file(file_path)

        local_pr.put_file(
            my_yanked_file_path,
            dirs=os.path.dirname(my_yanked_file_path[len(s3_pr.target_dir) + 1 :]),
        )

        r = requests.patch(
            f"http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/files/{puzzle_file['name']}/",
            json={
                "url": f"/resources/{puzzle_id}/{my_yanked_file_path[len(s3_pr.target_dir)+1:]}",
            },
        )
        if r.status_code != 200:
            raise Exception(f"move_all_from_s3 error.  Request failed. {r}")
        if is_destructive:
            s3_pr.purge_file(file_path)

        # Rate limiting to avoid going over the s3 request limits.
        sleep(0.1)


def main():
    """"""
    config_file = "site.cfg"

    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")

    args = docopt(__doc__)
    is_destructive = args["--destructive"]

    app = make_app(
        config=config_file,
        cookie_secret=cookie_secret,
    )

    with app.app_context():
        if current_app.config["LOCAL_PUZZLE_RESOURCES"]:
            move_all_from_s3(is_destructive=is_destructive)
        else:
            move_all_to_s3(is_destructive=is_destructive)


if __name__ == "__main__":
    main()
