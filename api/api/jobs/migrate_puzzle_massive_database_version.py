#!/usr/bin/env python
"""
Migrate to the next version for the Puzzle Massive database by finding any
python scripts found next to this script by globbing for
"migrate_puzzle_massive_database_version_[0-9][0-9][0-9].py"

Each script file should end with the database_version number that it migrates
from. Migrate scripts will only be executed if the current database_version
matches the version number in the script file name.  The database_version will
be incremented after successfully executing each script.
"""

import sys
import logging
from glob import glob
import os.path
import subprocess
import datetime

from api.app import db, make_app
from api.database import read_query_file, rowify
from api.tools import loadConfig, version_number

logging.basicConfig()
logger = logging.getLogger(os.path.basename(sys.argv[0]))


class MigrateError(Exception):
    """"""


class MigrateGapError(MigrateError):
    """"""


def get_next_migrate_script(migrate_scripts):
    "Returns the next migrate script that should execute."
    if len(migrate_scripts) == 0:
        raise MigrateError("migrate_scripts list is empty.")

    migrate_script = None
    sorted_migrate_scripts = migrate_scripts.copy()
    sorted_migrate_scripts.sort(key=version_number)

    cur = db.cursor()
    result = cur.execute(
        read_query_file("select_puzzle_massive_key.sql"), {"key": "database_version"}
    ).fetchall()
    if result:
        (result, _) = rowify(result, cur.description)
        database_version = result[0]["intvalue"]
    else:
        database_version = 0
    cur.close()

    # First time check
    if database_version == 0:
        if (
            os.path.basename(sorted_migrate_scripts[0])
            == f"migrate_puzzle_massive_database_version_{database_version:03}.py"
        ):
            return sorted_migrate_scripts[0]
        else:
            raise MigrateError(
                f"The database version was missing or set to 0, but the migrate_puzzle_massive_database_version_{database_version:03}.py was not included in the migrate scripts to run."
            )

    next_database_version = database_version + 1
    for item in sorted_migrate_scripts:
        if (
            os.path.basename(item)
            == f"migrate_puzzle_massive_database_version_{next_database_version:03}.py"
        ):
            migrate_script = item
            break
        if version_number(item) > next_database_version:
            raise MigrateGapError(
                f"Missing migrate_puzzle_massive_database_version_{next_database_version:03}.py"
            )

    return migrate_script


def main():
    config_file = "site.cfg"
    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")
    app = make_app(
        config=config_file, cookie_secret=cookie_secret, database_writable=True
    )

    logger.setLevel(logging.DEBUG if config["DEBUG"] else logging.INFO)

    with app.app_context():
        cur = db.cursor()

        # Always create the PuzzleMassive table in case it doesn't exist.
        cur.execute(read_query_file("create_table_puzzle_massive.sql"))
        db.commit()

        script_file = sys.argv[0]

        migrate_scripts = glob(
            f"{os.path.dirname(script_file)}/migrate_puzzle_massive_database_version_[0-9][0-9][0-9].py"
        )
        if len(migrate_scripts) == 0:
            logger.warning(
                f"No migrate scripts found for glob: '{os.path.dirname(script_file)}/migrate_puzzle_massive_database_version_[0-9][0-9][0-9].py'"
            )
            cur.close()
            sys.exit(0)

        next_migrate_script = get_next_migrate_script(migrate_scripts)
        sanity_count = 0
        while next_migrate_script:
            version = version_number(next_migrate_script)
            logger.info(
                f"Executing {next_migrate_script} to migrate from PuzzleMassive database version {version}."
            )
            logger.debug(f"sanity count {sanity_count}")
            sanity_count = sanity_count + 1

            # Execute the next_migrate_script
            try:
                output = subprocess.run(
                    [sys.executable, next_migrate_script],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as err:
                logger.debug(str(err))
                logger.error(f"Failed when executing {next_migrate_script}.")
                logger.info(f"\n{err.stdout.decode()}\n")
                logger.error(f"\n{err.stderr.decode()}\n")
                cur.close()
                sys.exit(1)
            logger.info(f"\n{output.stdout.decode()}\n")
            logger.info(f"\n{output.stderr.decode()}\n")

            # Bump the database_version assuming that the migrate script was
            # successful.
            now = datetime.datetime.utcnow().isoformat()
            logger.info(
                f"Successfully executed {next_migrate_script} and will now update database_version to be {version + 1}."
            )
            cur.execute(
                read_query_file("upsert_puzzle_massive.sql"),
                {
                    "key": "database_version",
                    "label": "Database Version",
                    "description": f"Puzzle Massive Database version updated on {now}. Only update this via the {script_file}",
                    "intvalue": version + 1,
                    "textvalue": None,
                    "blobvalue": None,
                },
            )
            db.commit()

            next_migrate_script = get_next_migrate_script(migrate_scripts)
            if sanity_count > len(migrate_scripts):
                logger.error(
                    "Exiting out of while loop for checking next migrate scripts."
                )
                break
        else:
            logger.info("PuzzleMassive database version is up to date.")

        cur.close()


if __name__ == "__main__":
    main()
