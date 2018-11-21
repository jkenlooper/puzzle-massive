"""
Meant to run periodically to migrate existing puzzles.  Will not handle rerendering puzzles; just changing their status to rebuild.
- If AWS S3 hosted puzzle resources; download original.jpg and create new preview_full if it isn't unsplash
- If preview_full is source.unsplash create custom size with api and update PuzzleFile
- If source.unsplash; update description with links to photographer and unsplash.  Include photo description on next line.
"""

import sqlite3
import os
import os.path
import sys
import time
import math
import random
from urlparse import urlparse

import boto3
import botocore

from api.app import db
from api.database import rowify, read_query_file
from api.tools import loadConfig

# Get the args and connect to the database
config_file = sys.argv[1]
config = loadConfig(config_file)

db_file = config['SQLITE_DATABASE_URI']
db = sqlite3.connect(db_file)

# set to not autocommit
db.isolation_level = None

# Check if bucket exists
s3_resource = boto3.resource('s3')
BUCKET_NAME = 'puzzle.massive.xyz'
bucket = s3_resource.Bucket(BUCKET_NAME)
exists = True
try:
    s3_resource.meta.client.head_bucket(Bucket=BUCKET_NAME)
except botocore.exceptions.ClientError as e:
    # If a client error is thrown, then check that it was a 404 error.
    # If it was a 404 error, then the bucket does not exist.
    error_code = e.response['Error']['Code']
    if error_code == '404':
        exists = False

s3 = boto3.client('s3')

# The unsplash API only allows for 50 requests an hour for demo apps.
HOUR_IN_SECONDS = 60 * 60
UNSPLASH_MAX_REQUESTS_PER_HOUR = 50
MAX_RANDOM_DELAY_SECONDS = 60 * 13
MIGRATE_INTERVAL = int(math.ceil(float(HOUR_IN_SECONDS) / float(UNSPLASH_MAX_REQUESTS_PER_HOUR)))

query_select_all_puzzles_to_migrate = read_query_file('_select-all-puzzles-to-migrate.sql')

query_select_puzzle_file_to_migrate_from_s3 = read_query_file('_select-puzzle-file-to-migrate-from-s3.sql')

query_select_puzzle_file_to_migrate_from_unsplash = read_query_file('_select-puzzle-file-to-migrate-from-unsplash.sql')

query_update_puzzle_file_original_null_url = read_query_file('_update-puzzle-file-original-null-url.sql')
query_update_puzzle_file_original_s3_url = read_query_file('_update-puzzle-file-original-s3-url.sql')

query_update_puzzle_file_url = read_query_file('_update-puzzle-file-url.sql')

def create_puzzle_dir(puzzle_id):
    puzzle_dir = os.path.join(config.get('PUZZLE_RESOURCES'), puzzle_id)
    try:
        os.mkdir(puzzle_dir)
    except OSError as err:
        if err.errno == 17:
            # The previous call most likely has created the puzzle_dir.
            pass
        else:
            raise err
    return puzzle_dir

def migrate_s3_puzzle(puzzle):
    """
    Download the file from S3 and update the url in the puzzle file.
    """
    if not exists:
        print("Bucket doesn't exist")
        return

    cur = db.cursor()

    puzzle_id = puzzle.get('puzzle_id')
    puzzle_dir = create_puzzle_dir(puzzle_id)
    url_components = urlparse(puzzle.get('url'))
    key = url_components.path[1:]
    file_name = os.path.basename(key)
    file_path = os.path.join(puzzle_dir, file_name)
    local_url = "/resources/{puzzle_id}/{file_name}".format(puzzle_id=puzzle_id, file_name=file_name)
    print("Downloading {}".format(os.path.join(puzzle_dir, os.path.basename(key))))
    s3.download_file(BUCKET_NAME, key, file_path)

    cur.execute(query_update_puzzle_file_url, {
        'puzzle': puzzle.get('puzzle'),
        'name': puzzle.get('name'),
        'url': local_url
        })

    print("{puzzle} migrating s3 puzzle file {name} ({puzzle_id}): {url}".format(**puzzle))

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

    # Update any original that have an empty url
    cur.execute(query_update_puzzle_file_original_null_url, {
        'puzzle': puzzle
    })

    # Update any original that have a '0' for url
    cur.execute(query_update_puzzle_file_original_s3_url, {
        'puzzle': puzzle
    })

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
            #time.sleep(delay)

def migrate_all():
    """
    Update all puzzle files that need to migrate their resources.
    """
    confirm = raw_input("Commit the transaction? y/n\n")
    cur = db.cursor()
    cur.execute("begin");
    print("begin transaction")
    result = cur.execute(query_select_all_puzzles_to_migrate).fetchall()
    if result:
        for item in result:
            migrate_next_puzzle(item[0])

    # while developing
    if confirm == 'y':
        cur.execute("commit");
        print("transaction has been committed")
    else:
        cur.execute("rollback");
        print("transaction has been rollbacked")

if __name__ == '__main__':
    migrate_all()
