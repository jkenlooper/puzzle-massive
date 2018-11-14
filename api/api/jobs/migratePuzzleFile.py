"""
Meant to run periodically to migrate existing puzzles.  Will not handle rerendering puzzles; just changing their status to rebuild.
- If AWS S3 hosted puzzle resources; download original.jpg and create new preview_full if it isn't unsplash
- If preview_full is source.unsplash create custom size with api and update PuzzleFile
- If source.unsplash; update description with links to photographer and unsplash.  Include photo description on next line.
"""

import sqlite3
import os
import sys
import time
import math
import random

from api.app import db
from api.database import rowify, read_query_file
from api.tools import loadConfig

# Get the args and connect to the database
config_file = sys.argv[1]
config = loadConfig(config_file)

db_file = config['SQLITE_DATABASE_URI']
db = sqlite3.connect(db_file)

# The unsplash API only allows for 50 requests an hour for demo apps.
HOUR_IN_SECONDS = 60 * 60
UNSPLASH_MAX_REQUESTS_PER_HOUR = 50
MAX_RANDOM_DELAY_SECONDS = 60 * 13
MIGRATE_INTERVAL = int(math.ceil(float(HOUR_IN_SECONDS) / float(UNSPLASH_MAX_REQUESTS_PER_HOUR)))

query_select_all_puzzles_to_migrate = read_query_file('_select-all-puzzles-to-migrate.sql')

query_select_puzzle_file_to_migrate_from_s3 = read_query_file('_select-puzzle-file-to-migrate-from-s3.sql')

query_select_puzzle_file_to_migrate_from_unsplash = read_query_file('_select-puzzle-file-to-migrate-from-unsplash.sql')

def migrate_s3_puzzle(puzzle):
    """
    Download the file from S3 and update the url in the puzzle file.
    """
    # TODO: migrate off of S3
    # original.jpg
    # preview_full
    # pieces.png
    # pzz.css
    print("{puzzle} migrating s3 puzzle file {name}: {url}".format(**puzzle))
    if puzzle.url == '0': # or just test if the name is 'original'?
        # TODO: the original.jpg url is '0' since it wasn't ever public
        pass

def migrate_unsplash_puzzle(puzzle):
    """
    Update description to match the requirments of using the unsplash photo.
    Update the hotlinked preview_full url with the utm params.
    """
    # TODO: Update description for unsplash photos.  May need to have description able to handle some HTML like anchor links? maybe strip tags?
    # Photo by Annie Spratt / Unsplash
    # [description]
    # TODO: fix preview_full url
    print("{puzzle} migrating unsplash puzzle file {name}: {url}".format(**puzzle))

def migrate_next_puzzle(puzzle):
    cur = db.cursor()

    result = cur.execute(query_select_puzzle_file_to_migrate_from_s3, {
        'puzzle': puzzle
        }).fetchall()
    if result:
        (result, col_names) = rowify(result, cur.description)
        for item in result:
            migrate_s3_puzzle(item)

    result = cur.execute(query_select_puzzle_file_to_migrate_from_unsplash, {
        'puzzle': puzzle,
        }).fetchall()
    if result:
        (result, col_names) = rowify(result, cur.description)
        for item in result:
            migrate_unsplash_puzzle(item)
            delay = MIGRATE_INTERVAL + random.randint(0, MAX_RANDOM_DELAY_SECONDS)
            print("sleeping for {} seconds".format(delay))
            time.sleep(delay)

def migrate_all():
    """
    Update all puzzle files that need to migrate their resources.
    """
    cur = db.cursor()
    result = cur.execute(query_select_all_puzzles_to_migrate).fetchall()
    if result:
        for item in result:
            migrate_next_puzzle(item[0])

if __name__ == '__main__':
    migrate_all()
