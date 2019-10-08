"Migrates 2.3.x to active-puzzles-only support"
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

    ## Update all existing puzzles that are IN_QUEUE to ACTIVE if they have recent m_date
    result = cur.execute("update Puzzle set status = 1 where status = 2 and strftime('%s', m_date) >= strftime('%s', 'now', '-7 days');")

    db.commit()
    cur.close()
