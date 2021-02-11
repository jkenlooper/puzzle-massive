from __future__ import absolute_import
from builtins import zip, bytes
import os
import time
import hashlib

from flask import current_app
from .app import db

PUZZLE_CREATE_TABLE_LIST = (
    "create_table_puzzle.sql",
    "create_table_piece.sql",
    "create_table_user.sql",
    "create_table_timeline.sql",
    "create_timeline_puzzle_index.sql",
    "create_timeline_timestamp_index.sql",
    "create_table_puzzle_file.sql",
    "create_table_bit_author.sql",
    "create_table_bit_expiration.sql",
    "create_table_bit_icon.sql",
    "create_table_attribution.sql",
    "create_table_license.sql",
    "create_table_puzzle_variant.sql",
    "create_table_puzzle_instance.sql",
    "create_table_user_puzzle.sql",
    "create_table_puzzle_feature_data.sql",
    "create_table_puzzle_feature.sql",
    "create_table_puzzle_puzzle_feature.sql",
    "create_table_player_account.sql",
    "create_table_name_register.sql",
)


def init_db():
    """Initialize a new database for testing purposes."""
    with current_app.app_context():
        # db = get_db()
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

        application_name = current_app.config.get("UNSPLASH_APPLICATION_NAME")
        ## Set initial licenses
        for statement in read_query_file("initial_licenses.sql").split(";"):
            cur.execute(statement, {"application_name": application_name})
            db.commit()

        ## Add fake bit icons
        def each(bit):
            for b in bit:
                yield b

        bits = [
            {"name": "fake-cat", "author": 1},
            {"name": "fake-dog", "author": 1},
            {"name": "fake-eel", "author": 2},
            {"name": "fake-bug", "author": 2},
        ]
        query = """
        INSERT OR REPLACE INTO BitIcon (author, name) VALUES (:author, :name);
        """
        cur.executemany(query, each(bits))
        db.commit()
        cur.close()


def rowify(l, description):
    d = []
    col_names = []
    if l != None and description != None:
        col_names = [x[0] for x in description]
        for row in l:
            d.append(dict(list(zip(col_names, row))))
    return (d, col_names)


# TODO: deprecate
def _fetch_sql_string(file_name):
    with current_app.open_resource(os.path.join("queries", file_name), mode="r") as f:
        return f.read()


def fetch_query_string(file_name):
    content = current_app.queries.get(file_name, None)

    if content == None:
        current_app.logger.info(
            "queries file: '%s' not available. Checking file system..." % file_name
        )
        file_path = os.path.join("queries", file_name)
        if os.path.isfile(file_path):
            with open(file_path, "r") as f:
                content = r.read()
                current_app.queries[file_name] = content
        else:
            raise Exception("File not found: {}".format(file_name))

    return content


def read_query_file(file_name):
    """
    Read the sql file content without requiring app context.  Useful for simple
    scripts to load the same query files from the root.
    """
    file_path = os.path.join("queries", file_name)
    if os.path.isfile(file_path):
        with open(file_path, "r") as f:
            return f.read()
    else:
        raise Exception("File not found: {}".format(file_path))


def generate_new_puzzle_id(name):
    """
    The puzzle_id has an increasing number prefix and then some hashed unique string.
    """
    cur = db.cursor()
    max_id = (
        cur.execute(fetch_query_string("select-next-puzzle-id.sql")).fetchone()[0] or 1
    )  # in case there are no puzzles found.
    d = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
    puzzle_id = "%i%s" % (
        max_id,
        hashlib.sha224(bytes("%s%s" % (name, d), "utf-8")).hexdigest()[0:9],
    )
    cur.close()
    return puzzle_id


def delete_puzzle_resources(puzzle_id):
    puzzle_dir = os.path.join(current_app.config["PUZZLE_RESOURCES"], puzzle_id)
    if not os.path.exists(puzzle_dir):
        return
    for (dirpath, dirnames, filenames) in os.walk(puzzle_dir, False):
        for filename in filenames:
            os.unlink(os.path.join(dirpath, filename))
        for dirname in dirnames:
            os.rmdir(os.path.join(dirpath, dirname))
    os.rmdir(puzzle_dir)
