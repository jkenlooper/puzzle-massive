import sqlite3
import os
import glob
import sys
#from sqlalchemy import create_engine

from api.tools import loadConfig
from api.database import PUZZLE_CREATE_TABLE_LIST, read_query_file

SET_ANONYMOUS_PLAYER_BIT = """ -- ANONYMOUS_USER_ID
UPDATE BitIcon SET user = 2 WHERE name = 'food-cookie';
"""


if __name__ == "__main__":

    # Get the args and create db
    config_file = sys.argv[1]
    config = loadConfig(config_file)

    db_file = config['SQLITE_DATABASE_URI']
    db = sqlite3.connect(db_file)

    application_name = config.get('UNSPLASH_APPLICATION_NAME')

    # TODO: Update to use sqlalchemy
    #db = create_engine(config['CHILL_DATABASE_URI'], echo=config['DEBUG'])
    cur = db.cursor()

    ## Create the new tables and populate with initial data
    query_files = list(PUZZLE_CREATE_TABLE_LIST)
    query_files.append('initial_puzzle_variant.sql')
    query_files.append('insert_initial_bit_expiration_round_2.sql')
    query_files.append('insert_initial_bit_author_and_anon_user.sql')

    for file_path in query_files:
        query = read_query_file(file_path)
        for statement in query.split(';'):
            cur.execute(statement)
            db.commit()

    ## Set initial licenses
    for statement in read_query_file('initial_licenses.sql').split(';'):
        cur.execute(statement, {
            'application_name': application_name
        })
        db.commit()

    ## Add each bit icon that is in the filesystem
    bits = []

    for s in glob.glob(os.path.join(config['MEDIA_BIT_ICONS_FOLDER'], 'source-*.txt')):
        root = os.path.splitext(os.path.basename(s))[0]
        group_name = root[root.index('-')+1:]
        for b in glob.glob(os.path.join(os.path.dirname(s), '64-%s-*.png' % group_name)):
            name = os.path.basename(b)[len(group_name)+4:-4]
            b_name = "-".join([group_name, name])

            bits.append({
                'name': b_name,
                'author': 2 if group_name == 'mackenzie' else 1
            })

    def each(bit):
        for b in bit:
            yield b

    cur = db.cursor()
    query = """
    INSERT OR REPLACE INTO BitIcon (author, name) VALUES (:author, :name);
    """
    cur.executemany(query, each(bits))
    db.commit()
    cur.execute(SET_ANONYMOUS_PLAYER_BIT)
    db.commit()
    cur.close()
