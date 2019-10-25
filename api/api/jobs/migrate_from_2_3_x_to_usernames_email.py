"Migrates 2.3.x to usernames and email support"
## Refer to docs/deployment.md

import sys
import sqlite3
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
            'cleanup_migrate_from_2_3_x_to_usernames_email.sql',
            'create_table_player_account.sql',
            ):
        for statement in read_query_file(filename).split(';'):
            cur.execute(statement)
            db.commit()

    db.commit()
    cur.close()
