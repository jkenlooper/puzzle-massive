"Migrates the bit icon name to new BitIcon table and sets the expiration."

# ./bin/py src/api/jobs/migrate_from_1_6_to_1_7.py chill.cfg

import sqlite3
import glob
import os

from api.app import db
from api.database import rowify
from api.create_database import SET_ANONYMOUS_PLAYER_BIT
from api.tools import loadConfig

if __name__ == '__main__':
    import sys

    # Get the args from the worker and connect to the database
    config_file = sys.argv[1]
    config = loadConfig(config_file)

    db_file = config['CHILL_DATABASE_URI']
    db = sqlite3.connect(db_file)

    cur = db.cursor()

    ## Create the new tables
    for file_path in (
            '../queries/cleanup_migrate.sql',
            '../queries/create_table_bit_author.sql',
            '../queries/create_table_bit_expiration.sql',
            '../queries/create_table_bit_icon.sql',
            '../queries/insert_initial_bit_expiration.sql',
            '../queries/insert_initial_bit_author_and_anon_user.sql'
            ):
        with open(os.path.normpath(os.path.join(os.path.dirname(__file__), file_path)), 'r') as f:
            for statement in f.read().split(';'):
                cur.execute(statement)
                db.commit()

    query_all_users_with_icons = """
    select * from User where icon != '';
    """
    (results, col_names) = rowify(cur.execute(query_all_users_with_icons, {}).fetchall(), cur.description)
    users_with_icons = results
    icon_to_user_mapping = {}

    for user in users_with_icons:
        ## add in the computed expiration based on m_date
        result = cur.execute("""
              SELECT datetime(:m_date, (
                SELECT be.extend FROM BitExpiration AS be
                  JOIN User AS u
                   WHERE u.score > be.score AND u.id = :id
                   ORDER BY be.score DESC LIMIT 1
                )
              ) as expiration;
        """, user).fetchone()
        if result[0]:
            user['bit_expires'] = result[0]
            icon_to_user_mapping[user['icon']] = user
    ## for each bit icon
    bits = []
    ## Previous commit had bit-icons as a symlink which may have caused an issue when reading the bit-icons folder.  The workaround is to just rename the bit-icons to 'hold' or something.
    for s in glob.glob(os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'media', 'bit-icons', 'source-*.txt')):
        root = os.path.splitext(os.path.basename(s))[0]
        group_name = root[root.index('-')+1:]
        for b in glob.glob(os.path.join(os.path.dirname(s), '64-%s-*.png' % group_name)):
            name = os.path.basename(b)[len(group_name)+4:-4]
            b_name = "-".join([group_name, name])

            user = icon_to_user_mapping.get(b_name, {})

            bits.append({
                'name': b_name,
                'user': user.get('id'),
                'expiration': user.get('bit_expires'),
                'author': 2 if group_name == 'mackenzie' else 1
            })

    def each(bit):
        for b in bit:
            yield b

    cur = db.cursor()
    query = """
    INSERT OR REPLACE INTO BitIcon (user, author, name, expiration) VALUES (:user, :author, :name, :expiration);
    """
    cur.executemany(query, each(bits))
    db.commit()
    cur.execute(SET_ANONYMOUS_PLAYER_BIT)
    db.commit()

    # Change the bit expiration for new players
    for file_path in (
            '../queries/insert_initial_bit_expiration_round_2.sql',
            ):
        with open(os.path.normpath(os.path.join(os.path.dirname(__file__), file_path)), 'r') as f:
            for statement in f.read().split(';'):
                cur.execute(statement)
                db.commit()


    cur.close()
