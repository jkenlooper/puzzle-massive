#!/usr/bin/env python

import sys
import os.path
import glob

import sqlite3
import yaml

from api.tools import loadConfig
from api.database import read_query_file


def add_bit_icons_in_file_system(db):
    "Add each bit icon that is in the filesystem"

    bits = []

    cur = db.cursor()
    select_author_id_query = read_query_file("_select-author_id-for-slug-name.sql")
    upsert_author_query = read_query_file("_insert_or_update_bit_author.sql")
    insert_or_replace_bit_icon_query = read_query_file(
        "_insert_or_replace_bit_icon.sql"
    )
    for source_file in glob.glob(
        os.path.join("source-media", "bit-icons", "source-*.yaml")
    ):
        root = os.path.splitext(os.path.basename(source_file))[0]
        group_name = root[root.index("-") + 1 :]
        with open(source_file, "r") as f:
            source = yaml.safe_load(f)
            cur.execute(
                upsert_author_query,
                {
                    "name": source["name"],
                    "slug_name": source["slug_name"],
                    "artist_document": source["artist_document"],
                },
            )
            db.commit()
            author_id = cur.execute(
                select_author_id_query, {"slug_name": source["slug_name"]}
            ).fetchone()[0]
            for bit_icon_file in glob.glob(
                os.path.join(os.path.dirname(source_file), f"{group_name}-*")
            ):
                bit_icon_name = os.path.splitext(os.path.basename(bit_icon_file))[0]
                bits.append({"name": bit_icon_name, "author": author_id})

    def each(bit):
        for b in bit:
            yield b

    cur.executemany(insert_or_replace_bit_icon_query, each(bits))
    db.commit()


def main():
    """"""
    config_file = "site.cfg"

    config = loadConfig(config_file)

    db_file = config["SQLITE_DATABASE_URI"]
    db = sqlite3.connect(db_file)

    add_bit_icons_in_file_system(db)


if __name__ == "__main__":
    main()
