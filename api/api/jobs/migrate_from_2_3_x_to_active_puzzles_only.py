"Migrates 2.3.x to active-puzzles-only support"
## Refer to docs/deployment.md

import sys
import sqlite3
import logging

from api.app import db
from api.database import rowify, read_query_file
from api.tools import loadConfig
from api.constants import (
    ACTIVE,
    IN_QUEUE,
    QUEUE_NEW,
    QUEUE_END_OF_LINE
)

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

    ## Update all existing puzzles that are IN_QUEUE to ACTIVE if they are not new
    result = cur.execute("update Puzzle set status = :ACTIVE where status = :IN_QUEUE and m_date is not null;", dict(**locals()))

    ## Prevent retiring any existing puzzles right away by bumping the modified date
    result = cur.execute("update Puzzle set m_date = datetime('now', '-1 day') where status = :ACTIVE and m_date is not null and m_date > datetime('now', '-6 days');", dict(**locals()))

    ## Set existing new puzzles to be in the right queue
    result = cur.execute("update Puzzle set queue = :QUEUE_NEW where m_date is null and status = :IN_QUEUE;", dict(**locals()))

    ## Any remaining puzzles should be set to end of line for the queue
    result = cur.execute("update Puzzle set queue = :QUEUE_END_OF_LINE where queue > :QUEUE_END_OF_LINE;", dict(**locals()))

    db.commit()
    cur.close()
