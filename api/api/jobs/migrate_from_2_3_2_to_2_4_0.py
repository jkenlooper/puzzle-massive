"Migrates 2.3.2 to 2.4.0 which includes puzzle-instances, new-player, active-puzzles, usernames, and email"
# TODO: Improve by using docopt for documenting this script.
# TODO: Create a Puzzle Massive database version so the migrate script can use
# that when running.  It should update the version afterwards.
# TODO: Create a migrate script runner?

## Refer to docs/deployment.md

import sqlite3
import glob
import os
import sys
import logging

from api.app import db
from api.database import rowify, read_query_file
from api.tools import loadConfig
from api.constants import CLASSIC, ACTIVE, IN_QUEUE, QUEUE_NEW, QUEUE_END_OF_LINE


# Get the args and connect to the database
config_file = sys.argv[1]
config = loadConfig(config_file)

db_file = config["SQLITE_DATABASE_URI"]
db = sqlite3.connect(db_file)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if config["DEBUG"] else logging.INFO)

if __name__ == "__main__":

    cur = db.cursor()

    ## Create the new tables
    for filename in (
        "cleanup_migrate_from_2_3_2_to_2_4_0.sql",
        "create_table_puzzle_variant.sql",
        "create_table_puzzle_instance.sql",
        "create_table_user_puzzle.sql",
        "create_table_player_account.sql",
        "create_table_name_register.sql",
        "initial_puzzle_variant.sql",
    ):
        for statement in read_query_file(filename).split(";"):
            cur.execute(statement)
            db.commit()

    classic_variant = cur.execute(
        read_query_file("select-puzzle-variant-id-for-slug.sql"), {"slug": CLASSIC}
    ).fetchone()[0]

    ## Populate the puzzle instances
    result = cur.execute("SELECT id FROM Puzzle;").fetchall()
    if result:
        logger.info(
            "migrating existing {} puzzles to all be classic variants in the instance table".format(
                len(result)
            )
        )
        for id in map(lambda x: x[0], result):
            logger.debug("id: {}".format(id))
            cur.execute(
                "insert into PuzzleInstance (original, instance, variant) values (:puzzle, :instance, :variant);",
                {"puzzle": id, "instance": id, "variant": classic_variant},
            )

    ## Update all players cookie_expires date
    result = cur.execute("update User set cookie_expires=date('now', '-14 days');")

    ## Update all existing puzzles that are IN_QUEUE to ACTIVE if they are not new
    result = cur.execute(
        "update Puzzle set status = :ACTIVE where status = :IN_QUEUE and m_date is not null;",
        dict(**locals()),
    )

    ## Prevent retiring any existing puzzles right away by bumping the modified date
    result = cur.execute(
        "update Puzzle set m_date = datetime('now', '-1 day') where status = :ACTIVE and m_date is not null and m_date > datetime('now', '-6 days');",
        dict(**locals()),
    )

    ## Set existing new puzzles to be in the right queue
    result = cur.execute(
        "update Puzzle set queue = :QUEUE_NEW where m_date is null and status = :IN_QUEUE;",
        dict(**locals()),
    )

    ## Any remaining puzzles should be set to end of line for the queue
    result = cur.execute(
        "update Puzzle set queue = :QUEUE_END_OF_LINE where queue > :QUEUE_END_OF_LINE;",
        dict(**locals()),
    )

    db.commit()
    cur.close()
