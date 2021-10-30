#!/usr/bin/env python
"""migrate_puzzle_massive_database_version.py - Migrate to the next version for the Puzzle Massive database

Usage: migrate_puzzle_massive_database_version.py [--config <file>]
       migrate_puzzle_massive_database_version.py --help

Options:
    -h --help           Show this screen.
    --config <file>     Set config file. [default: site.cfg]
"""

import sys
import logging
from glob import glob
import os.path
from docopt import docopt

from api.app import db, make_app
from api.database import read_query_file, rowify
from api.tools import loadConfig, version_number

logging.basicConfig()
logger = logging.getLogger(os.path.basename(sys.argv[0]))


class MigrateError(Exception):
    ""


class MigrateGapError(MigrateError):
    ""



def get_next_migrate_script(migrate_scripts):
    "Returns the next migrate script that should execute."
    if len(migrate_scripts) == 0:
        raise MigrateError("migrate_scripts list is empty.")

    migrate_script = None
    sorted_migrate_scripts = migrate_scripts.copy()
    sorted_migrate_scripts.sort(key=version_number)

    cur = db.cursor()
    result = cur.execute(read_query_file("select_puzzle_massive_key.sql"), {"key": "database_version"}).fetchall()
    if result:
        (result, _) = rowify(result, cur.description)
        database_version = result[0]["intvalue"]
    else:
        database_version = 0
    cur.close()

    # First time check
    if database_version == 0:
        if os.path.basename(sorted_migrate_scripts[0]) == f"migrate_puzzle_massive_database_version_{database_version:03}.py":
            return sorted_migrate_scripts[0]
        else:
            raise MigrateError(f"The database version was missing or set to 0, but the migrate_puzzle_massive_database_version_{database_version:03}.py was not included in the migrate scripts to run.")

    next_database_version = database_version + 1
    for item in sorted_migrate_scripts:
        if os.path.basename(item) == f"migrate_puzzle_massive_database_version_{next_database_version:03}.py":
            migrate_script = item
            break
        if version_number(item) > next_database_version:
            raise MigrateGapError(f"Missing migrate_puzzle_massive_database_version_{next_database_version:03}.py")

    return migrate_script


if __name__ == "__main__":
    args = docopt(__doc__)
    config_file = args["--config"]
    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")
    app = make_app(config=config_file, cookie_secret=cookie_secret, database_writable=True)

    logger.setLevel(logging.DEBUG if config["DEBUG"] else logging.INFO)

    with app.app_context():
        cur = db.cursor()

        # Always create the PuzzleMassive table in case it doesn't exist.
        cur.execute(read_query_file("create_table_puzzle_massive.sql"))
        db.commit()

        script_file = sys.argv[0]

        migrate_scripts = glob(f"{os.path.dirname(script_file)}/migrate_puzzle_massive_database_version_[0-9][0-9][0-9].py")
        if len(migrate_scripts) == 0:
            logger.warning(f"No migrate scripts found for glob: '{os.path.dirname(script_file)}/migrate_puzzle_massive_database_version_[0-9][0-9][0-9].py'")
            cur.close()
            sys.exit(0)

        next_migrate_script = get_next_migrate_script(migrate_scripts)
        sanity_count = 0
        while next_migrate_script:
            version = version_number(next_migrate_script)
            logger.info(f"Executing {next_migrate_script} to migrate from PuzzleMassive database version {version}.")
            logger.debug(f"sanity count {sanity_count}")
            sanity_count = sanity_count + 1

            # TODO: execute the next_migrate_script

            cur.execute(read_query_file("upsert_puzzle_massive.sql"), {
                "key": "database_version",
                "label": "Database Version",
                "description": "The version that the Puzzle Massive Database is currently at.",
                "intvalue": version + 1,
                "textvalue": None,
                "blobvalue": None
            })
            db.commit()

            next_migrate_script = get_next_migrate_script(migrate_scripts)
            if sanity_count > len(migrate_scripts):
                logger.error("Exiting out of while loop for checking next migrate scripts.")
                break
        else:
            logger.info("PuzzleMassive database version is up to date.")

        cur.close()
