#!/usr/bin/env bash

set -eu -o pipefail

ENVIRONMENT=$1
SRVDIR=$2
DATABASEDIR=$3
PORTREGISTRY=$4
ARCHIVEDIR=$5
CACHEDIR=$6

# shellcheck source=/dev/null
source "$PORTREGISTRY"

source .env

# The .env file has some environment variables that can be added if the app
# requires them. Uncomment this line as well as the EXAMPLE_PUBLIC_KEY below.
#source ".env"

if test "$ENVIRONMENT" == 'development'; then
  DEBUG=True
else
  DEBUG=False
fi

cat <<HERE

# The site.cfg file is used to configure a flask app.  Refer to the flask
# documentation for other configurations.  The below are used specifically by
# Chill.

# Set the HOST to 0.0.0.0 for being an externally visible server.
HOST = '127.0.0.1'
PORT = $PORTCHILL

HOSTAPI = '127.0.0.1'
PORTAPI = $PORTAPI

# The other app for divulging piece movements
HOSTDIVULGER = '127.0.0.1'
PORTDIVULGER = $PORTDIVULGER

HOSTREDIS = '127.0.0.1'
PORTREDIS = $PORTREDIS
REDIS_URI = 'redis://127.0.0.1:${PORTREDIS}/0/'

# Valid SQLite URL forms are:
#   sqlite:///:memory: (or, sqlite://)
#   sqlite:///relative/path/to/file.db
#   sqlite:////absolute/path/to/file.db
# http://docs.sqlalchemy.org/en/latest/core/engines.html
CHILL_DATABASE_URI = "sqlite:///${DATABASEDIR}db"
# TODO: for now use a path instead since it uses sqlite strictly
SQLITE_DATABASE_URI = "${DATABASEDIR}db"

# Archive directory for storing puzzle timeline. Not directly accessible by the
# public.
PUZZLE_ARCHIVE = "${ARCHIVEDIR}"

# Resource directory for storing puzzle resources. Only some paths are
# accessible via web.  Used for storing uploaded puzzles.
PUZZLE_RESOURCES = "${SRVDIR}resources"

# If using the ROOT_FOLDER then you will need to set the PUBLIC_URL_PREFIX to
# something other than '/'.
#PUBLIC_URL_PREFIX = "/"

# If setting the ROOT_FOLDER:
PUBLIC_URL_PREFIX = "/site"

# The ROOT_FOLDER is used to send static files from the '/' route.  This will
# conflict with the default value for PUBLIC_URL_PREFIX. Any file or directory
# within the ROOT_FOLDER will be accessible from '/'.  The default is not
# having anything set.
ROOT_FOLDER = "root"

# The document folder is an optional way of storing content outside of the
# database.  It is used with the custom filter 'readfile' which can read the
# file from the document folder into the template.  If it is a Markdown file
# you can also use another filter to parse the markdown into HTML with the
# 'markdown' filter. For example:
# {{ 'llamas-are-cool.md'|readfile|markdown }}
DOCUMENT_FOLDER = "documents"

# The media folder is used to send static files that are not related to the
# 'theme' of a site.  This usually includes images and videos that are better
# served from the file system instead of the database. The default is not
# having this set to anything.
MEDIA_FOLDER = "media"

# The bit-icons are served from a different directory.  Refer to the nginx conf.
MEDIA_BIT_ICONS_FOLDER = "${SRVDIR}media/bit-icons"

# The media path is where the files in the media folder will be accessible.  In
# templates you can use the custom variable: 'media_path' which will have this
# value.
# {{ media_path }}llama.jpg
# or:
# {{ url_for('send_media_file', filename='llama.jpg') }}
MEDIA_PATH = "/media/"

# When creating a stand-alone static website the files in the MEDIA_FOLDER are
# only included if they are linked to from a page.  Set this to True if all the
# files in the media folder should be included in the FREEZER_DESTINATION.
#MEDIA_FREEZE_ALL = False

# The theme is where all the front end resources like css, js, graphics and
# such that make up the theme of a website. The THEME_STATIC_FOLDER is where
# these files are located and by default nothing is set here.
THEME_STATIC_FOLDER = "dist"

# Set a THEME_STATIC_PATH for routing the theme static files with.  It's useful
# to set a version number within this path to easily do cache-busting.  In your
# templates you can use the custom variable:
# {{ theme_static_path }}llama.css
# or:
# {{ url_for('send_theme_file', filename='llama.css') }}
# to get the url to a file in the theme static folder.
#THEME_STATIC_PATH = "/theme/v0.0.1/"

import json
PACKAGEJSON = json.load(open('package.json'))
VERSION = json.load(open('package.json'))['version']
THEME_STATIC_PATH = "/theme/{0}/".format(VERSION or '0')

# Where the jinja2 templates for the site are located.  Will default to the app
# template_folder if not set.
THEME_TEMPLATE_FOLDER = "templates"

# Where all the custom SQL queries and such are located.  Chill uses a few
# built-in ones and they can be overridden by adding a file with the same name
# in here. To do much of anything with Chill you will need to add some custom
# SQL queries and such to load data into your templates.
THEME_SQL_FOLDER = "queries"

# Helpful to have this set to True if you want to fix stuff.
DEBUG=$DEBUG

# Caching with Flask-Cache
CACHE_NO_NULL_WARNING = True
#CACHE_TYPE = "null"
#CACHE_TYPE = "simple"
CACHE_TYPE = "filesystem"
CACHE_DEFAULT_TIMEOUT = 50
CACHE_THRESHOLD = 300
CACHE_DIR = "${CACHEDIR}"

# For creating a stand-alone static website that you can upload without
# requiring an app to run it. This will use Frozen-Flask.
# The path to the static/frozen website will be put.
FREEZER_DESTINATION = "frozen"
FREEZER_BASE_URL = "http://puzzle.massive.xyz/"

# Unsplash
UNSPLASH_APPLICATION_ID = "${UNSPLASH_APPLICATION_ID}"
UNSPLASH_APPLICATION_NAME = "${UNSPLASH_APPLICATION_NAME}"
UNSPLASH_SECRET = "${UNSPLASH_SECRET}"

SECURE_COOKIE_SECRET = "${SECURE_COOKIE_SECRET}"

# Temporary until the puzzle contributor role exists
NEW_PUZZLE_CONTRIB = "${NEW_PUZZLE_CONTRIB}"

# Email config
SMTP_HOST="${SMTP_HOST}"
SMTP_PORT="${SMTP_PORT}"
SMTP_USER="${SMTP_USER}"
SMTP_PASSWORD="${SMTP_PASSWORD}"
EMAIL_SENDER="${EMAIL_SENDER}"
EMAIL_MODERATOR="${EMAIL_MODERATOR}"

HERE
