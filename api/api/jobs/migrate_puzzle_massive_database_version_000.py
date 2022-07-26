#!/usr/bin/env python
"""
Add support for automatically rewarding puzzle instance slots. This only adds an
index to the existing User_Puzzle table.
"""

import os
import sys
import logging

from api.app import db, make_app
from api.database import read_query_file
from api.tools import loadConfig

logging.basicConfig()
logger = logging.getLogger(os.path.basename(sys.argv[0]))


def migrate(config):
    "Migrate the sqlite3 database from the current database_version."
    cur = db.cursor()

    for filename in [
        "create_user_puzzle_index.sql",
    ]:
        cur.execute(read_query_file(filename))
        db.commit()

    cur.close()


def main():
    config_file = "site.cfg"
    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")
    app = make_app(
        config=config_file, cookie_secret=cookie_secret, database_writable=True
    )

    logger.setLevel(logging.DEBUG if config["DEBUG"] else logging.INFO)

    with app.app_context():
        migrate(config)


if __name__ == "__main__":
    main()
