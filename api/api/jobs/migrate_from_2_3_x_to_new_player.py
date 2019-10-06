"Migrates 2.3.x to new-player support"
## Refer to docs/deployment.md

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

    ## Update all players cookie_expires date
    result = cur.execute("update User set cookie_expires=date('now', '-14 days');")

    db.commit()
    cur.close()
