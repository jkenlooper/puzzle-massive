"Migrates 2.0.1 to 2.1.0"
# TODO: Improve by using docopt for documenting this script.
# TODO: Create a Puzzle Massive database version so the migrate script can use
# that when running.  It should update the version afterwards.
# TODO: Create a migrate script runner?

## Refer to docs/deployment.md

##Follow blue-green deployment
# ...

##Transfer old server data
# ...

##Migrate database
# python api/api/jobs/migrate_from_2_0.py site.cfg

##All done (mostly)
# At this point the app can be started and accept traffic.  The rest of the
# commands can be run in the background in order to slowly update data for
# puzzle files.

##Add s3 credentials

##Run the migrate puzzle file script which will take a long time because it is
##limited by unsplash API request limits.
# nohup python api/api/jobs/migratePuzzleFile.py site.cfg &

import sqlite3
import glob
import os
import sys

from api.app import db
from api.database import rowify, read_query_file
from api.tools import loadConfig

# Get the args and connect to the database
config_file = sys.argv[1]
config = loadConfig(config_file)

db_file = config["SQLITE_DATABASE_URI"]
db = sqlite3.connect(db_file)

application_name = config.get("UNSPLASH_APPLICATION_NAME")

if __name__ == "__main__":

    cur = db.cursor()

    ## Create the new tables
    for filename in (
        "cleanup_migrate_from_2_0.sql",
        "create_table_attribution.sql",
        "create_table_license.sql",
        "initial_licenses.sql",
        "alter_puzzle_file_add_attribution.sql",
    ):
        for statement in read_query_file(filename).split(";"):
            cur.execute(statement, {"application_name": application_name})
            db.commit()

    cur.close()
