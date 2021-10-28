import sqlite3
import sys
import logging

from api.app import db
from api.database import read_query_file
from api.tools import loadConfig


# Get the args and connect to the database
config_file = sys.argv[1]
config = loadConfig(config_file)

db_file = config["SQLITE_DATABASE_URI"]

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if config["DEBUG"] else logging.INFO)

if __name__ == "__main__":

    cur = db.cursor()

    # Update
    for filename in [
        "create_user_puzzle_index.sql",
    ]:
        for statement in read_query_file(filename).split(";"):
            try:
                cur.execute(statement)
            except sqlite3.OperationalError as err:
                # Ignore sqlite error here if the slug_name column on BitAuthor
                # has already been added.
                logger.warning(f"Ignoring sqlite error: {err}")
            db.commit()

    cur.close()
