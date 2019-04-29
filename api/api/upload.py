from __future__ import print_function
from builtins import bytes
import os
import re
import time
import hashlib
import threading
import requests
import subprocess

import sqlite3
from PIL import Image
from flask import current_app, redirect, request, make_response, abort
from flask.views import MethodView
from werkzeug.utils import secure_filename, escape
from werkzeug.urls import url_fix

from api.app import db
from api.database import rowify, fetch_query_string, read_query_file
from api.constants import COMPLETED, NEEDS_MODERATION, PUBLIC
from api.user import user_id_from_ip, user_not_banned

# Not allowing anything other then jpg to protect against potential picture bombs.
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg'])

def submit_puzzle(pieces, bg_color, user, permission, description, link, upload_file):
    """
    Submit a puzzle to be reviewed.  Generates the puzzle_id and original.jpg.
    """
    unsplash_image_thread = None

    puzzle_id = None
    cur = db.cursor()
    query = """select max(id)*13 from Puzzle;"""
    max_id = cur.execute(query).fetchone()[0] or 1 # in case there are no puzzles found.

    unsplash_match = re.search(r"unsplash.com/photos/([^/]+)", link)
    if link and unsplash_match:
        if not current_app.config.get('UNSPLASH_APPLICATION_ID'):
            abort(400)

        d = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
        filename = unsplash_match.group(1)
        u_id = "%s" % (hashlib.sha224(bytes("%s%s" % (filename, d), 'utf-8')).hexdigest()[0:9])
        puzzle_id = "unsplash{filename}-mxyz-{u_id}".format(filename=filename, u_id=u_id)

        # Create puzzle dir
        puzzle_dir = os.path.join(current_app.config.get('PUZZLE_RESOURCES'), puzzle_id)
        os.mkdir(puzzle_dir)

        # Download the unsplash image
        unsplash_image_thread = UnsplashPuzzleThread(puzzle_id, filename, current_app.config.get('UNSPLASH_APPLICATION_ID'), current_app.config.get('SQLITE_DATABASE_URI'))
    else:
        if not upload_file:
            cur.close()
            abort(400)
        filename = secure_filename(upload_file.filename)
        filename = filename.lower()

        # Check the filename to see if the extension is allowed
        if os.path.splitext(filename)[1][1:].lower() not in ALLOWED_EXTENSIONS:
            cur.close()
            abort(400)

        d = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
        puzzle_id = "%i%s" % (max_id, hashlib.sha224(bytes("%s%s" % (filename, d), 'utf-8')).hexdigest()[0:9])

        # Create puzzle dir
        puzzle_dir = os.path.join(current_app.config.get('PUZZLE_RESOURCES'), puzzle_id)
        os.mkdir(puzzle_dir)

        # Convert the uploaded file to jpg
        upload_file_path = os.path.join(puzzle_dir, filename)
        upload_file.save(upload_file_path)

        # verify the image file format
        identify_format = subprocess.check_output(['identify', '-format', '%m', upload_file_path], encoding='utf-8')
        identify_format = identify_format.lower()
        if identify_format not in ALLOWED_EXTENSIONS:
            os.unlink(upload_file_path)
            os.rmdir(puzzle_dir)
            cur.close()
            abort(400)


        # Abort if imagemagick fails converting the image to jpg
        try:
            subprocess.check_call(['convert', upload_file_path, '-quality', '85%', '-format', 'jpg', os.path.join(puzzle_dir, 'original.jpg')])
        except subprocess.CalledProcessError:
            os.unlink(upload_file_path)
            os.rmdir(puzzle_dir)
            abort(400)
        os.unlink(upload_file_path)

        # The preview_full image is only created in the pieceRender process.

    query = """select max(queue)+1 from Puzzle where permission = 0;"""
    count = cur.execute(query).fetchone()[0]
    if (not count):
      count = 1

    d = {'puzzle_id':puzzle_id,
        'pieces':pieces,
        'name':filename,
        'link':link,
        'description':description,
        'bg_color':bg_color,
        'owner':user,
        'queue':count,
        'status': NEEDS_MODERATION,
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
    print(puzzle)
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

    db.commit()
    cur.close()

    if unsplash_image_thread:
        # Go download the unsplash image and update the db
        unsplash_image_thread.start()

    return puzzle_id

class PuzzleUploadView(MethodView):
    """
    Handle uploaded puzzle images
    """
    decorators = [user_not_banned]

    def post(self):
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # Only allow valid contributor
        if args.get('contributor', None) != current_app.config.get('NEW_PUZZLE_CONTRIB'):
            abort(403)

        # Check pieces arg
        try:
            pieces = int(args.get('pieces', current_app.config['MINIMUM_PIECE_COUNT']))
        except ValueError as err:
            abort(400)
        if pieces < current_app.config['MINIMUM_PIECE_COUNT']:
            abort(400)

        # Check bg_color
        color_regex = re.compile('.*?#?([a-f0-9]{6}|[a-f0-9]{3}).*?', re.IGNORECASE)
        bg_color = args.get('bg_color', '#808080')[:50]
        color_match = color_regex.match(bg_color)
        if (color_match):
            bg_color = "#{0}".format(color_match.group(1))
        else:
            bg_color = "#808080"

        user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP')))

        # All puzzles are public
        permission = PUBLIC
        #permission = int(args.get('permission', PUBLIC))
        #if permission != PUBLIC:
        #    permission = PUBLIC

        description = escape(args.get('description', ''))[:1000]

        # Check link and validate
        link = url_fix(args.get('link', ''))[:1000]

        upload_file = request.files.get('upload_file', None)

        puzzle_id = submit_puzzle(pieces, bg_color, user, permission, description, link, upload_file)

        return redirect('/chill/site/puzzle/{0}/'.format(puzzle_id), code=303)


class AdminPuzzlePromoteSuggestedView(MethodView):
    """
    Handle promoting a suggested puzzle to be in needs moderation status.
    """
    def post(self):
        "Route is protected by basic auth in nginx"
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        puzzle_id = args.get('puzzle_id')
        if not puzzle_id:
            abort(400)

        # Check pieces arg
        try:
            pieces = int(args.get('pieces', current_app.config['MINIMUM_PIECE_COUNT']))
        except ValueError as err:
            abort(400)
        if pieces < current_app.config['MINIMUM_PIECE_COUNT']:
            abort(400)

        # Check bg_color
        color_regex = re.compile('.*?#?([a-f0-9]{6}|[a-f0-9]{3}).*?', re.IGNORECASE)
        bg_color = args.get('bg_color', '#808080')[:50]
        color_match = color_regex.match(bg_color)
        if (color_match):
            bg_color = "#{0}".format(color_match.group(1))
        else:
            bg_color = "#808080"

        # All puzzles are public
        permission = PUBLIC
        #permission = int(args.get('permission', PUBLIC))
        #if permission != PUBLIC:
        #    permission = PUBLIC

        description = escape(args.get('description', ''))[:1000]

        # Check link and validate
        link = url_fix(args.get('link', ''))[:1000]

        upload_file = request.files.get('upload_file', None)

        # TODO: get the owner of the suggested puzzle
        cur = db.cursor()
        result = cur.execute(fetch_query_string('_select-owner-for-suggested-puzzle.sql'), {
            'puzzle_id': puzzle_id
            }).fetchone()
        if not result:
            abort(400)
        owner = result[0]

        new_puzzle_id = submit_puzzle(pieces, bg_color, owner, permission, description, link, upload_file)

        # Update the status of this suggested puzzle to be the suggested done
        # status
        cur.execute(fetch_query_string('_update-suggested-puzzle-to-done-status.sql'), {
            'puzzle_id': puzzle_id
        })
        db.commit()
        cur.close()

        return redirect('/chill/site/puzzle/{0}/'.format(new_puzzle_id), code=303)


class UnsplashPuzzleThread(threading.Thread):
    def __init__(self, puzzle_id, photo, application_id, db_file):
        threading.Thread.__init__(self)
        self.puzzle_id = puzzle_id
        self.photo = photo
        self.application_id = application_id
        self.db_file = db_file
        self.puzzle_resources = current_app.config.get('PUZZLE_RESOURCES')
        self.application_name = current_app.config.get('UNSPLASH_APPLICATION_NAME')
    def run(self):
        r = requests.get('https://api.unsplash.com/photos/%s' % self.photo, params={
            'client_id': self.application_id,
            'w': 384,
            'h': 384,
            'fit': 'max'
            }, headers={'Accept-Version': 'v1'})
        data = r.json()

        self.add_puzzle(data)

    def add_puzzle(self, data):
        db = sqlite3.connect(self.db_file)
        cur = db.cursor()
        description = escape(data.get('description', None))

        puzzle_dir = os.path.join(self.puzzle_resources, self.puzzle_id)
        filename = os.path.join(puzzle_dir, 'original.jpg')
        f = open(filename, 'w+b')

        links = data.get('links')
        if not links:
            raise Exception('Unsplash returned no links')
        download = links.get('download')
        if not download:
            raise Exception('Unsplash returned no download')
        r = requests.get(download)
        f.write(r.content)
        f.close()

        d = {'puzzle_id':self.puzzle_id,
            'link':None,
            'description':description}
        cur.execute("""update Puzzle set
        link = :link,
        description = :description
        where puzzle_id = :puzzle_id;
        """, d)
        db.commit()

        puzzle = rowify(cur.execute("select id from Puzzle where puzzle_id = :puzzle_id;", {'puzzle_id':self.puzzle_id}).fetchall(), cur.description)[0][0]['id']

        # Set preview full url and fallback to small
        preview_full_url = data.get('urls', {}).get('custom', data.get('urls', {}).get('small'))
        # Use the max version to keep the image ratio and not crop it.
        preview_full_url = re.sub('fit=crop', 'fit=max', preview_full_url)

        insert_attribution_unsplash_photo = read_query_file('insert_attribution_unsplash_photo.sql')

        # Not using url_fix on the user.links.html since it garbles the '@'.
        result = cur.execute(insert_attribution_unsplash_photo, {
            'title': 'Photo',
            'author_link': "{user_link}?utm_source={application_name}&utm_medium=referral".format(
                user_link=data.get('user').get('links').get('html'),
                application_name=self.application_name),
            'author_name': data.get('user').get('name'),
            'source': "{photo_link}?utm_source={application_name}&utm_medium=referral".format(
                photo_link=data.get('links').get('html'),
                application_name=self.application_name)
        })

        attribution_id = result.lastrowid

        insert_file = "update PuzzleFile set url = :url, attribution = :attribution where puzzle = :puzzle and name = :name;"
        cur.execute(insert_file, {
            'puzzle': puzzle,
            'attribution': attribution_id,
            'name': 'preview_full',
            'url': preview_full_url
            })

        db.commit()
        cur.close()
