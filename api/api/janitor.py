"""Janitor - Run the puzzle_cleanup jobs
Usage: puzzle-massive-janitor [--config <file>]
       puzzle-massive-janitor --help

Options:
    -h --help           Show this screen.
    --config <file>     Set config file. [default: site.cfg]
"""
from builtins import map
import os
import sys
from docopt import docopt

import requests
from flask import current_app
from rq import Worker, Queue, Connection

from api.app import make_app
from api.tools import loadConfig, get_redis_connection
from api.constants import RENDERING_FAILED, BUGGY_UNLISTED

# Preload libs
from api.jobs import convertPiecesToDB, piece_forker, piece_reset, unsplash_image

listen = ["puzzle_cleanup", "unsplash_image_fetch"]


def handle_fail(job, exception, exception_func, traceback):
    current_app.logger.warning("Handle janitor fail {0}".format(job))
    current_app.logger.debug("args {0}".format(job.args))
    current_app.logger.debug("job {0}".format(job))
    current_app.logger.debug("job func_name {0}".format(job.func_name))
    if job.func_name == "api.jobs.unsplash_image.add_photo_to_puzzle":
        puzzle_id = job.args[0]
        r = requests.patch(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                HOSTAPI=current_app.config["HOSTAPI"],
                PORTAPI=current_app.config["PORTAPI"],
                puzzle_id=puzzle_id,
            ),
            json={
                "status": RENDERING_FAILED,
            },
        )
        if r.status_code != 200:
            current_app.logger.warning(
                f"Puzzle details api error. Could not set puzzle status to rendering failed. Skipping {puzzle_id}"
            )
    # TODO: Fix handling of errors on puzzle reset pieces
    elif job.func_name == "api.jobs.piece_reset.reset_puzzle_pieces_and_handle_errors":
        puzzle_id = job.args[0]
        r = requests.patch(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/details/".format(
                HOSTAPI=current_app.config["HOSTAPI"],
                PORTAPI=current_app.config["PORTAPI"],
                puzzle_id=puzzle_id,
            ),
            json={
                "status": BUGGY_UNLISTED,
            },
        )
        if r.status_code != 200:
            current_app.logger.warning(
                f"Puzzle details api error. Could not set puzzle status to buggy unlisted. Skipping {puzzle_id}"
            )


def main():
    """"""
    args = docopt(__doc__)
    config_file = args["--config"]
    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")
    redis_connection = get_redis_connection(config, decode_responses=False)
    app = make_app(config=config_file, cookie_secret=cookie_secret)

    with app.app_context():
        with Connection(redis_connection):
            worker = Worker(list(map(Queue, listen)))

            # If the render process has an exception
            worker.push_exc_handler(handle_fail)

            worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
