import sqlite3
import sys
from glob import glob
import os.path
import logging

from api.tools import loadConfig
from api.database import (
    PUZZLE_CREATE_TABLE_LIST,
    read_query_file,
    puzzle_features_init_list,
)
from api.tools import (
    get_latest_version_based_on_migrate_scripts,
)


if __name__ == "__main__":

    logging.basicConfig()
    logger = logging.getLogger(os.path.basename(sys.argv[0]))

    # Get the args and create db
    config_file = sys.argv[1]
    config = loadConfig(config_file)

    db_file = config["SQLITE_DATABASE_URI"]
    db = sqlite3.connect(db_file)

    application_name = config.get("UNSPLASH_APPLICATION_NAME")

    cur = db.cursor()

    # Create the new tables and populate with initial data
    query_files = list(PUZZLE_CREATE_TABLE_LIST)
    query_files.append("initial_puzzle_variant.sql")
    query_files.append("insert_initial_admin_user.sql")
    query_files.append("insert_initial_anon_user.sql")

    for file_path in query_files:
        query = read_query_file(file_path)
        for statement in query.split(";"):
            cur.execute(statement)
            db.commit()

    # Set initial licenses
    for statement in read_query_file("initial_licenses.sql").split(";"):
        cur.execute(statement, {"application_name": application_name})
        db.commit()

    # Set puzzle features that are enabled
    puzzle_features = config.get("PUZZLE_FEATURES", set())
    print(f"Enabling puzzle features: {puzzle_features}")
    for query_file in puzzle_features_init_list(puzzle_features):
        cur.execute(read_query_file(query_file))
        db.commit()

    latest_version = 0
    migrate_scripts = glob(f"{os.path.dirname(sys.argv[0])}/jobs/migrate_puzzle_massive_database_version_[0-9][0-9][0-9].py")
    if len(migrate_scripts) == 0:
        logger.warning(f"{os.path.dirname(sys.argv[0])}/jobs/migrate_puzzle_massive_database_version_[0-9][0-9][0-9].py")
    else:
        latest_version = get_latest_version_based_on_migrate_scripts(migrate_scripts)
    cur.execute(read_query_file("upsert_puzzle_massive.sql"), {
        "key": "database_version",
        "label": "Database Version",
        "description": "The version that the Puzzle Massive Database is currently at.",
        "intvalue": latest_version,
        "textvalue": None,
        "blobvalue": None
    })
    db.commit()

    cur.close()
