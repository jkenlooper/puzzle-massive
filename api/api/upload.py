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
from api.database import rowify
from api.constants import COMPLETED, NEEDS_MODERATION
from api.user import user_id_from_ip

#permissions
PUBLIC   = 0  # obvious...

# Should match policy in /etc/ImageMagick-6/policy.xml
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'webp'])

class PuzzleUploadView(MethodView):
    """
    Handle uploaded puzzle images
    """
    def post(self):
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # Only allow valid contributor
        if args.get('contributor', None) != current_app.config.get('NEW_PUZZLE_CONTRIB'):
            abort(403)

        # Check pieces arg
        pieces = args.get('pieces', 100)
        if pieces < 2:
            abort(400)

        # Check bg_color
        color_regex = re.compile('.*?#?([a-f0-9]{6}|[a-f0-9]{3}).*?', re.IGNORECASE)
        bg_color = args.get('bg_color', '#808080')[:50]
        color_match = color_regex.match(bg_color)
        if (color_match):
            bg_color = "#{0}".format(color_match.group(1))
        else:
            bg_color = "#808080"

        # Verify user is logged in
        user = current_app.secure_cookie.get(u'user') or user_id_from_ip(request.headers.get('X-Real-IP'))
        if user == None:
            abort(403)

        # All puzzles are public
        permission = PUBLIC
        #permission = int(args.get('permission', PUBLIC))
        #if permission != PUBLIC:
        #    permission = PUBLIC

        description = escape(args.get('description', ''))

        # Check link and validate
        unsplash_image_thread = None
        link = url_fix(args.get('link', ''))

        puzzle_id = None
        cur = db.cursor()
        query = """select max(id)*13 from Puzzle;"""
        max_id = cur.execute(query).fetchone()[0] or 1 # in case there are no puzzles found.

        unsplash_match = re.search(r"unsplash.com/photos/([^/]+)", link)
        if link and unsplash_match:
            d = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
            filename = unsplash_match.group(1)
            u_id = "%s" % (hashlib.sha224("%s%s" % (filename, d)).hexdigest()[0:9])
            puzzle_id = "unsplash{filename}-mxyz-{u_id}".format(filename=filename, u_id=u_id)

            # Create puzzle dir
            puzzle_dir = os.path.join(current_app.config.get('PUZZLE_RESOURCES'), puzzle_id)
            os.mkdir(puzzle_dir)

            # Download the unsplash image
            unsplash_image_thread = UnsplashPuzzleThread(puzzle_id, filename, current_app.config.get('UNSPLASH_APPLICATION_ID'), current_app.config.get('SQLITE_DATABASE_URI'))
        else:
            upload_file = request.files.get('upload_file', None)
            if not upload_file:
                abort(400)
            filename = secure_filename(upload_file.filename)
            filename = filename.lower()

            # Check the filename to see if the extension is allowed
            if os.path.splitext(filename)[1][1:] not in ALLOWED_EXTENSIONS:
                abort(400)

            d = time.strftime("%Y_%m_%d.%H_%M_%S", time.localtime())
            puzzle_id = "%i%s" % (max_id, hashlib.sha224("%s%s" % (filename, d)).hexdigest()[0:9])

            # Create puzzle dir
            puzzle_dir = os.path.join(current_app.config.get('PUZZLE_RESOURCES'), puzzle_id)
            os.mkdir(puzzle_dir)

            # Convert the uploaded file to jpg
            upload_file_path = os.path.join(puzzle_dir, filename)
            upload_file.save(upload_file_path)
            # Abort if imagemagick is converting an image that is not websafe
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
        print puzzle
        puzzle = puzzle['id']

        insert_file = "insert into PuzzleFile (puzzle, name, url) values (:puzzle, :name, :url);"
        cur.execute(insert_file, {
            'puzzle': puzzle,
            'name': 'original',
            'url': '' # Not a public file
            })

        insert_file = "insert into PuzzleFile (puzzle, name, url) values (:puzzle, :name, :url);"
        cur.execute(insert_file, {
            'puzzle': puzzle,
            'name': 'preview_full',
            'url': '/resources/{0}/preview_full.jpg'.format(puzzle_id)
            })

        db.commit()

        if unsplash_image_thread:
            # Go download the unsplash image and update the db
            unsplash_image_thread.start()

        return redirect('/chill/site/puzzle/{0}/'.format(puzzle_id), code=303)

class UnsplashPuzzleThread(threading.Thread):
    def __init__(self, puzzle_id, photo, application_id, db_file):
        threading.Thread.__init__(self)
        self.puzzle_id = puzzle_id
        self.photo = photo
        self.application_id = application_id
        self.db_file = db_file
        self.puzzle_resources = current_app.config.get('PUZZLE_RESOURCES')
    def run(self):
        r = requests.get('https://api.unsplash.com/photos/%s' % self.photo, params={
            'client_id': self.application_id
            }, headers={'Accept-Version': 'v1'})
        data = r.json()

        self.add_puzzle(data)

    def add_puzzle(self, data):
        db = sqlite3.connect(self.db_file)
        cur = db.cursor()
        link = url_fix(data.get('links').get('html'))
        description = escape("Photo by: %s" % (data.get('user').get('name')))

        puzzle_dir = os.path.join(self.puzzle_resources, self.puzzle_id)
        filename = os.path.join(puzzle_dir, 'original.jpg')
        f = open(filename, 'w')

        r = requests.get(data.get('links').get('download'))
        f.write(r.content)
        f.close()

        d = {'puzzle_id':self.puzzle_id,
            'link':link,
            'description':description}
        cur.execute("""update Puzzle set
        link = :link,
        description = :description
        where puzzle_id = :puzzle_id;
        """, d)
        db.commit()

        puzzle = rowify(cur.execute("select id from Puzzle where puzzle_id = :puzzle_id;", {'puzzle_id':self.puzzle_id}).fetchall(), cur.description)[0][0]['id']

        # Request a custom size now that the photo dimensions are known
        img_short = int((float(min(data['width'], data['height'])) / float(max(data['width'], data['height']))) * 384)
        img_long = 384
        preview_width = img_long if data['width'] > data['height'] else img_short
        preview_height = img_short if data['width'] > data['height'] else img_long
        r = requests.get('https://api.unsplash.com/photos/%s' % self.photo, params={
            'client_id': self.application_id,
            'w': preview_width,
            'h': preview_height
            }, headers={'Accept-Version': 'v1'})
        custom_data = r.json()

        # Create source.unsplash.com url as a fallback in case custom is not there
        m = re.match(r"unsplash(.+?)(-mxyz-.*)*$", self.puzzle_id)
        source_unsplash = '/'.join(["https://source.unsplash.com", m.group(1), '384x384'])
        source_unsplash = re.sub('{}$'.format('384x384'), 'x'.join([str(preview_width), str(preview_height)]), source_unsplash)

        # Set preview full url and fallback to source.unsplash.com
        preview_full_url = custom_data.get('urls', {}).get('custom', source_unsplash)

        insert_file = "update PuzzleFile set url = :url where puzzle = :puzzle and name = :name;"
        cur.execute(insert_file, {
            'puzzle': puzzle,
            'name': 'preview_full',
            'url': preview_full_url
            })

        db.commit()
