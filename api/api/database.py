from __future__ import absolute_import
from builtins import zip, bytes
import os
import time
import hashlib
import re

from flask import current_app
from .app import db
from api.puzzle_resource import PuzzleResource

PUZZLE_CREATE_TABLE_LIST = (
    "create_table_puzzle.sql",
    "create_puzzle_puzzle_id_index.sql",
    "create_table_piece.sql",
    "create_piece_puzzle_index.sql",
    "create_table_user.sql",
    "create_user_ip_index.sql",
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
    "create_table_puzzle_feature.sql",
    "create_table_puzzle_feature_data.sql",
    "create_table_player_account.sql",
    "create_table_name_register.sql",
)


def puzzle_features_init_list(puzzle_features):
    """
    Features for puzzles that can be enabled for a puzzle site are listed here.
    Each one uses the 'slug' as the feature with the name and description fields.
    They are enabled via the site.cfg PUZZLE_FEATURES variable which is set via the
    .env file.  Creating and updating features are done by executing these SQL
    files.
    """
    all_feature_queries_init = [
        "puzzle-feature-reset-enabled.sql",
        "puzzle-feature--hidden-preview.sql",
        "puzzle-feature--secret-message.sql",
    ]
    # The enable list will be filtered based on what is in PUZZLE_FEATURES set.
    all_feature_queries_enable = [
        "puzzle-feature-enable--hidden-preview.sql",
        "puzzle-feature-enable--secret-message.sql",
    ]

    def is_feature_enabled(query_file):
        m = re.match("puzzle-feature-enable--(.*).sql", query_file)
        if m:
            return m.group(1) in puzzle_features or "all" in puzzle_features
        else:
            return False

    return all_feature_queries_init + list(
        filter(is_feature_enabled, all_feature_queries_enable)
    )


def init_db():
    """Initialize a new database for testing purposes."""
    with current_app.app_context():
        # db = get_db()
        cur = db.cursor()

        ## Create the new tables and populate with initial data
        query_files = list(PUZZLE_CREATE_TABLE_LIST)
        query_files.append("initial_puzzle_variant.sql")
        query_files.append("insert_initial_admin_user.sql")
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

        ## Add fake bit authors
        upsert_author_query = read_query_file("_insert_or_update_bit_author.sql")
        for i in range(1, 3):
            cur.execute(
                upsert_author_query,
                {
                    "name": f"test-author{i}",
                    "slug_name": f"testauthor{i}",
                    "artist_document": f"testauthor{i}.md",
                },
            )
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
        query = read_query_file("_insert_or_replace_bit_icon.sql")
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


def delete_puzzle_resources(puzzle_id, is_local_resource=True, exclude_regex=None):
    pr = PuzzleResource(puzzle_id, current_app.config, is_local_resource=is_local_resource)
    pr.purge(exclude_regex=exclude_regex)
