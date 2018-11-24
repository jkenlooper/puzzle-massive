"Migrates ..."

# python api/api/jobs/migrate_from_2_0.py

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

db_file = config['SQLITE_DATABASE_URI']
db = sqlite3.connect(db_file)

application_name = config.get('UNSPLASH_APPLICATION_NAME')

if __name__ == '__main__':

    cur = db.cursor()

    ## Create the new tables
    for filename in (
            'cleanup_migrate_from_2_0.sql',
            'create_table_attribution.sql',
            'create_table_license.sql',
            'initial_licenses.sql',
            'alter_puzzle_file_add_attribution.sql',
            ):
        for statement in read_query_file(filename).split(';'):
            cur.execute(statement, {
                'application_name': application_name
            })
            db.commit()

    cur.close()
