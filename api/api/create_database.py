import sqlite3
import sys

# from sqlalchemy import create_engine

from api.tools import loadConfig
from api.database import PUZZLE_CREATE_TABLE_LIST, read_query_file

if __name__ == "__main__":

    # Get the args and create db
    config_file = sys.argv[1]
    config = loadConfig(config_file)

    db_file = config["SQLITE_DATABASE_URI"]
    db = sqlite3.connect(db_file)

    application_name = config.get("UNSPLASH_APPLICATION_NAME")

    # TODO: Update to use sqlalchemy
    # db = create_engine(config['CHILL_DATABASE_URI'], echo=config['DEBUG'])
    cur = db.cursor()

    ## Create the new tables and populate with initial data
    query_files = list(PUZZLE_CREATE_TABLE_LIST)
    query_files.append("initial_puzzle_variant.sql")
    query_files.append("insert_initial_anon_user.sql")

    for file_path in query_files:
        query = read_query_file(file_path)
        for statement in query.split(";"):
            cur.execute(statement)
            db.commit()

    ## Set initial licenses
    for statement in read_query_file("initial_licenses.sql").split(";"):
        cur.execute(statement, {"application_name": application_name})
        db.commit()

    cur.close()
