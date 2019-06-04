"Migrates 2.3.x to puzzle-instances support"
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


# Get the args and connect to the database
config_file = sys.argv[1]
config = loadConfig(config_file)

db_file = config['SQLITE_DATABASE_URI']
db = sqlite3.connect(db_file)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if config['DEBUG'] else logging.INFO)

if __name__ == '__main__':

    cur = db.cursor()

    ## Create the new tables
    for filename in (
            'cleanup_migrate_from_2_3_x_to_puzzle_instances.sql',
            'create_table_puzzle_variant.sql',
            'create_table_puzzle_instance.sql',
            'initial_puzzle_variant.sql',
            ):
        for statement in read_query_file(filename).split(';'):
            cur.execute(statement)
            db.commit()

    classic_variant = cur.execute("select id from PuzzleVariant where slug = 'classic';").fetchone()[0]

    ## Populate the puzzle instances
    result = cur.execute("SELECT id FROM Puzzle;").fetchall()
    if result:
        logger.info("migrating existing {} puzzles to all be classic variants in the instance table".format(len(result)))
        for id in map(lambda x: x[0], result):
            logger.debug("id: {}".format(id))
            cur.execute("insert into PuzzleInstance (original, instance, variant) values (:puzzle, :instance, :variant);", {"puzzle": id, "instance": id, "variant": classic_variant})

    db.commit()
    cur.close()
