"""puzzle-massive-testdata - Generate random puzzle data for testing

Usage: puzzle-massive-testdata players [--count=<n>]
       puzzle-massive-testdata puzzles [--count=<n>] [--pieces=<n>] [--min-pieces=<n>] [--size=<s>]
       puzzle-massive-testdata instances [--count=<n>] [--pieces=<n>] [--min-pieces=<n>]
       puzzle-massive-testdata --help

Options:
    -h --help         Show this screen.
    --count=<n>       Create this many items [default: 1]
    --size=<s>        Random image size (passed to imagemagick resize opt) [default: 180x180!]
    --pieces=<n>      Piece count max [default: 9]
    --min-pieces=<n>  Piece count min [default: 0]

Subcommands:
    players     - Generate some random player data
    puzzles     - Create random images and create puzzles
    instances   - Create instances of existing puzzles for random players
"""

import sys
import os
import time
from uuid import uuid4
import hashlib
import subprocess
from random import randint
import sqlite3

import redis
from rq import Queue
from docopt import docopt

from api.tools import loadConfig
from api.user import generate_user_login
from api.constants import (
    ACTIVE,
    CLASSIC,
    COMPLETED,
    FROZEN,
    IN_QUEUE,
    IN_RENDER_QUEUE,
    NEEDS_MODERATION,
    NEW_USER_STARTING_POINTS,
    PUBLIC,
    REBUILD,
    RENDERING,
    QUEUE_NEW,
)
from api.database import rowify, PUZZLE_CREATE_TABLE_LIST, read_query_file, generate_new_puzzle_id

args = docopt(__doc__, version='0.0')

# Get the args and create db
config_file = 'site.cfg'
config = loadConfig(config_file)

db_file = config['SQLITE_DATABASE_URI']
db = sqlite3.connect(db_file)

redisConnection = redis.from_url(config.get('REDIS_URI', 'redis://localhost:6379/0/'), decode_responses=True)
createqueue = Queue('puzzle_create', connection=redisConnection)



QUERY_USER_ID_BY_LOGIN = """
select id from User where ip = :ip and login = :login;
"""

def generate_users(count):
    def generate_name(user_id):
        # TODO: Use generated names from https://www.name-generator.org.uk/
        return "Random Name for " + str(user_id)

    cur = db.cursor()

    for index in range(count):
        ip = '.'.join(map(lambda x: str(randint(0,255)), range(4)))
        score = randint(0, 15000)
        login = generate_user_login()
        query = """insert into User (points, score, login, m_date, ip) values
                (:points, :score, :login, datetime('now'), :ip)"""
        cur.execute(query, {'ip': ip, 'login': login, 'points': NEW_USER_STARTING_POINTS, 'score': score})
        result = cur.execute(QUERY_USER_ID_BY_LOGIN, {'ip':ip, 'login':login}).fetchall()
        (result, col_names) = rowify(result, cur.description)
        user_id = result[0]['id']

        # Claim a random bit icon
        cur.execute(read_query_file('claim_random_bit_icon.sql'), {'user': user_id})

        # Randomly Add slots
        for chance in range(randint(0, 1)):
            slotcount = randint(1, 6)
            if slotcount == 6:
                slotcount = randint(1,50)
            if slotcount == 50:
                slotcount = randint(50,250)
            for slot in range(slotcount):
                cur.execute(read_query_file("add-new-user-puzzle-slot.sql"), {'player': user_id})

        # Randomly assign player names
        chance_for_name = randint(0, 5)
        if chance_for_name == 5:
            display_name = generate_name(user_id)
            name = display_name.lower()
            cur.execute(read_query_file('add-user-name-on-name-register-for-player.sql'), {
                'player_id': user_id,
                'name': name,
                'display_name': display_name,
            })


    cur.close()
    db.commit()


def generate_puzzles(count=1, size="180x180!", min_pieces=0, max_pieces=9, user=3):
    cur = db.cursor()
    for index in range(count):
        link = ''
        description = ''
        bg_color = '#444444'
        permission = PUBLIC
        if min_pieces:
            pieces = randint(min_pieces, max_pieces)
        else:
            pieces = max_pieces
        filename = 'random-{}.png'.format(str(uuid4()))
        d = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
        puzzle_id = "random-{}".format(hashlib.sha224(bytes("%s%s" % (filename, d), 'utf-8')).hexdigest()[0:30])

        # Create puzzle dir
        puzzle_dir = os.path.join(config.get('PUZZLE_RESOURCES'), puzzle_id)
        os.mkdir(puzzle_dir)

        # Create random image
        file_path = os.path.join(puzzle_dir, filename)
        subprocess.check_call(['convert', '-size', '200x150', 'plasma:fractal', file_path])
        subprocess.check_call(['convert', file_path, '-paint', '10', '-blur',
                              '0x5', '-paint', '10', '-filter', 'box',
                               '-resize', size, '+repage',
                               '-auto-level', '-quality', '85%', '-format',
                               'jpg', os.path.join(puzzle_dir, 'original.jpg')])
        os.unlink(file_path)

        # Insert puzzle directly to render queue instead of setting status to NEEDS_MODERATION
        d = {'puzzle_id':puzzle_id,
            'pieces':pieces,
            'name':filename,
            'link':link,
            'description':description,
            'bg_color':bg_color,
            'owner':user,
            'queue':QUEUE_NEW,
            'status': IN_RENDER_QUEUE,
            'permission':permission}
        cur.execute("""insert into Puzzle (
        puzzle_id,
        pieces,
        name,
        link,
        description,
        bg_color,
        owner,
        queue,
        status,
        permission) values
        (:puzzle_id,
        :pieces,
        :name,
        :link,
        :description,
        :bg_color,
        :owner,
        :queue,
        :status,
        :permission);
        """, d)
        db.commit()

        puzzle = rowify(cur.execute("select id from Puzzle where puzzle_id = :puzzle_id;", {'puzzle_id':puzzle_id}).fetchall(), cur.description)[0][0]
        puzzle = puzzle['id']

        insert_file = "insert into PuzzleFile (puzzle, name, url) values (:puzzle, :name, :url);"
        cur.execute(insert_file, {
            'puzzle': puzzle,
            'name': 'original',
            'url': '/resources/{0}/original.jpg'.format(puzzle_id) # Not a public file (only on admin page)
            })

        insert_file = "insert into PuzzleFile (puzzle, name, url) values (:puzzle, :name, :url);"
        cur.execute(insert_file, {
            'puzzle': puzzle,
            'name': 'preview_full',
            'url': '/resources/{0}/preview_full.jpg'.format(puzzle_id)
            })

        classic_variant = cur.execute(read_query_file("select-puzzle-variant-id-for-slug.sql"), {"slug": CLASSIC}).fetchone()[0]
        cur.execute(read_query_file("insert-puzzle-instance.sql"), {"original": puzzle, "instance": puzzle, "variant": classic_variant})

        db.commit()
        print("pieces: {pieces} {puzzle_id}".format(**locals()))

    puzzles = rowify(cur.execute(read_query_file("select-puzzles-in-render-queue.sql"),
        {'IN_RENDER_QUEUE': IN_RENDER_QUEUE,
         'REBUILD': REBUILD})
        .fetchall(), cur.description)[0]
    print("found {0} puzzles to render".format(len(puzzles)))

    # push each puzzle to artist job queue
    for puzzle in puzzles:
        # push puzzle to artist job queue
        job = createqueue.enqueue_call(
            func='api.jobs.pieceRenderer.render', args=([puzzle]), result_ttl=0,
            timeout='24h'
        )

    cur.close()

def generate_puzzle_instances(count=1, min_pieces=0, max_pieces=9):
    cur = db.cursor()
    for index in range(count):
        bg_color = '#444444'
        permission = PUBLIC
        if min_pieces:
            pieces = randint(min_pieces, max_pieces)
        else:
            pieces = max_pieces
        result = cur.execute(read_query_file("select-random-player-with-available-user-puzzle-slot.sql")).fetchone()[0]
        if result:
            player = result
            # select a random original puzzle

            result = cur.execute(read_query_file("select-random-puzzle-for-new-puzzle-instance.sql"), {
                'ACTIVE': ACTIVE,
                'IN_QUEUE': IN_QUEUE,
                'COMPLETED': COMPLETED,
                'FROZEN': FROZEN,
                'REBUILD': REBUILD,
                'IN_RENDER_QUEUE': IN_RENDER_QUEUE,
                'RENDERING': RENDERING,
                'PUBLIC': PUBLIC}).fetchall()
            if not result:
                print('no puzzle found')
                continue

            (result, col_names) = rowify(result, cur.description)
            originalPuzzleData = result[0]

            filename = 'random-{}.png'.format(str(uuid4()))
            d = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
            puzzle_id = "rnd-instance-{}".format(hashlib.sha224(bytes("%s%s" % (filename, d), 'utf-8')).hexdigest()[0:30])

            # Create puzzle dir
            puzzle_dir = os.path.join(config.get('PUZZLE_RESOURCES'), puzzle_id)
            os.mkdir(puzzle_dir)

            # Insert puzzle directly to render queue
            d = {'puzzle_id':puzzle_id,
                'pieces':pieces,
                'name':originalPuzzleData['name'],
                'link':originalPuzzleData['link'],
                'description':originalPuzzleData['description'],
                'bg_color':bg_color,
                'owner':player,
                'queue':QUEUE_NEW,
                'status': IN_RENDER_QUEUE,
                'permission':permission}
            cur.execute("""insert into Puzzle (
            puzzle_id,
            pieces,
            name,
            link,
            description,
            bg_color,
            owner,
            queue,
            status,
            permission) values
            (:puzzle_id,
            :pieces,
            :name,
            :link,
            :description,
            :bg_color,
            :owner,
            :queue,
            :status,
            :permission);
            """, d)
            db.commit()

            result = cur.execute("select * from Puzzle where puzzle_id = :puzzle_id;", {'puzzle_id': puzzle_id}).fetchall()
            if not result:
                raise Exception('no puzzle instance')

            (result, col_names) = rowify(result, cur.description)
            puzzleData = result[0]
            puzzle = puzzleData['id']

            classic_variant = cur.execute(read_query_file("select-puzzle-variant-id-for-slug.sql"), {"slug": CLASSIC}).fetchone()[0]
            cur.execute(read_query_file("insert-puzzle-instance.sql"), {"original": originalPuzzleData['id'], "instance": puzzle, "variant": classic_variant})

            cur.execute(read_query_file("fill-user-puzzle-slot.sql"), {'player': player, 'puzzle': puzzle})

            db.commit()
            print("pieces: {pieces} {puzzle_id}".format(**locals()))

            job = createqueue.enqueue_call(
                func='api.jobs.pieceRenderer.render', args=([puzzleData]), result_ttl=0,
                timeout='24h'
            )
    cur.close()


def main():
    count = int(args.get('--count'))
    size = args.get('--size')
    max_pieces = int(args.get('--pieces'))
    min_pieces = int(args.get('--min-pieces'))

    if args.get('players'):
        print('Creating {} players'.format(count))
        generate_users(count)

    elif args.get('puzzles'):
        print('Creating {count} puzzles at {size} with up to {max_pieces} pieces'.format(count=count, size=size, max_pieces=max_pieces, min_pieces=min_pieces))
        generate_puzzles(count=count, size=size, min_pieces=min_pieces, max_pieces=max_pieces)

    elif args.get('instances'):
        print('Creating {count} puzzle instances with up to {max_pieces} pieces'.format(count=count, max_pieces=max_pieces, min_pieces=min_pieces))
        generate_puzzle_instances(count=count, min_pieces=min_pieces, max_pieces=max_pieces)

if __name__ == "__main__":
    main()
