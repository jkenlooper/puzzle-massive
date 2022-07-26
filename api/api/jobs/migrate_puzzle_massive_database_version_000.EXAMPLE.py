#!/usr/bin/env python
"""
Example sqlite database migration script. The script file name should end with
the database_version that it will migrate from. It will automatically be
executed when the migrate_puzzle_massive_database_version.py script is run and
the current database_version matches the version for this script file name.
"""

import sqlite3
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

    # Example script!
    # Copy it and rename it based on the database_version it will migrate from.
    # Modify as needed.
    logger.debug("Example debug message.")
    logger.info(f"Hello, this is an example log message for the {sys.argv[0]} script.")
    logger.warning("Uhh... warning message.")
    logger.error(
        "Oh no! Something didn't work! The script should run sys.exit('Abandon ship!') or something."
    )
    sys.exit(
        "\nERROR: Example script should be copied and modified to correctly run.\n"
    )  # Remove this

    # Execute the sql found in these files in the queries directory.
    for filename in [
        "example_that_modifies_the_database.sql",
        "another_example.sql",
    ]:
        if True:
            cur.execute(read_query_file(filename))
            db.commit()
        # Or split up each one as separate statements
        if False:
            for statement in read_query_file(filename).split(";"):
                # Optionally ignore errors if that is needed.
                try:
                    cur.execute(statement)
                except sqlite3.OperationalError as err:
                    logger.warning(f"Ignoring sqlite error: {err}")
                db.commit()

    # Or run other commands on the database to modify things as needed.

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
