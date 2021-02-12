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

    ## Update
    for filename in (
        "cleanup_migrate_from_2_9_2_to_2_10_0.sql",
        "alter_bit_author_for_migrate_from_2_9_2_to_2_10_0.sql",
        "create_table_puzzle_feature.sql",
        "create_table_puzzle_feature_data.sql",
    ):
        for statement in read_query_file(filename).split(";"):
            try:
                cur.execute(statement)
            except sqlite3.OperationalError as err:
                # Ignore sqlite error here if the slug_name column on BitAuthor
                # has already been added.
                logger.warning(f"Ignoring sqlite error: {err}")
            db.commit()

    cur.close()
