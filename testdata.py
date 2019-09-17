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
    RENDERING
)
from api.database import rowify, PUZZLE_CREATE_TABLE_LIST, read_query_file, generate_new_puzzle_id

QUERY_USER_ID_BY_LOGIN = """
select id from User where ip = :ip and login = :login;
"""

# Get the args and create db
config_file = sys.argv[1]
config = loadConfig(config_file)

db_file = config['SQLITE_DATABASE_URI']
db = sqlite3.connect(db_file)

redisConnection = redis.from_url(config.get('REDIS_URI', 'redis://localhost:6379/0/'), decode_responses=True)
createqueue = Queue('puzzle_create', connection=redisConnection)

def generate_users(count):
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
    cur.close()
    db.commit()

def generate_puzzles(count=1, size="180x180!", pieces=9, user=3):
    cur = db.cursor()
    for index in range(count):
        link = ''
        description = ''
        bg_color = '#444444'
        permission = PUBLIC
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
        query = """select max(queue)+1 from Puzzle where permission = 0;"""
        queuecount = cur.execute(query).fetchone()[0]
        if (not queuecount):
          queuecount = 1
        d = {'puzzle_id':puzzle_id,
            'pieces':pieces,
            'name':filename,
            'link':link,
            'description':description,
            'bg_color':bg_color,
            'owner':user,
            'queue':queuecount,
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
        print(puzzle_id)

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

def generate_puzzle_instances(count=1, pieces=9):
    cur = db.cursor()
    for index in range(count):
        bg_color = '#444444'
        permission = PUBLIC
        result = cur.execute(read_query_file("select-random-player-with-available-user-puzzle-slot.sql")).fetchone()[0]
        if result:
            player = result
            print(player)
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
            query = """select max(queue)+1 from Puzzle where permission = 0;"""
            queuecount = cur.execute(query).fetchone()[0]
            if (not queuecount):
              queuecount = 1

            d = {'puzzle_id':puzzle_id,
                'pieces':pieces,
                'name':originalPuzzleData['name'],
                'link':originalPuzzleData['link'],
                'description':originalPuzzleData['description'],
                'bg_color':bg_color,
                'owner':player,
                'queue':queuecount,
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
            print(puzzle_id)

            job = createqueue.enqueue_call(
                func='api.jobs.pieceRenderer.render', args=([puzzleData]), result_ttl=0,
                timeout='24h'
            )
    cur.close()


if __name__ == "__main__":
    generate_users(500)
    generate_puzzles(count=500, size="180x180!", pieces=9)
    generate_puzzles(count=10, size="800x500!", pieces=200)
    generate_puzzles(count=5, size="1800x1800!", pieces=900)
    generate_puzzle_instances(count=5, pieces=900)
    generate_puzzle_instances(count=20, pieces=200)
    generate_puzzle_instances(count=500, pieces=9)
