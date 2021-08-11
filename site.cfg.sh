#!/usr/bin/env bash

set -eu -o pipefail

ENVIRONMENT=$1
DATABASEDIR=$2
PORTREGISTRY=$3
SRVDIR=$4
ARCHIVEDIR=$5
CACHEDIR=$6
PURGEURLLIST=$7

# shellcheck source=/dev/null
source "$PORTREGISTRY"

source .env

HOSTCHILL=${HOSTCHILL:-'127.0.0.1'}
HOSTCACHE=${HOSTCACHE:-'127.0.0.1'}
HOSTORIGIN=${HOSTORIGIN:-'127.0.0.1'}
# The HOSTAPI should not be externally available.
# Keep HOSTAPI as localhost (127.0.0.1)
HOSTAPI=${HOSTAPI:-'127.0.0.1'}
# The HOSTPUBLISH should not be externally available.
# Keep HOSTPUBLISH as localhost (127.0.0.1)
HOSTPUBLISH=${HOSTPUBLISH:-'127.0.0.1'}
HOSTDIVULGER=${HOSTDIVULGER:-'127.0.0.1'}
HOSTSTREAM=${HOSTSTREAM:-'127.0.0.1'}
HOSTREDIS=${HOSTREDIS:-'127.0.0.1'}
# The redis db is by default 0 and the redis db used for unit tests is 1
REDIS_DB=0

DATE=$(date)

if test "$ENVIRONMENT" == 'development'; then
  DEBUG=True
else
  DEBUG=False
fi
HOSTNAME="'${DOMAIN_NAME}'"

cat <<HERE
# File generated from $0
# on ${DATE}

# The site.cfg file is used to configure a flask app.  Refer to the flask
# documentation for other configurations.  The below are used specifically by
# Chill.

# Set the HOST to 0.0.0.0 for being an externally visible server.
HOST = '$HOSTCHILL'
HOSTNAME = $HOSTNAME
SITE_PROTOCOL = 'http'
PORT = $PORTCHILL

HOSTCHILL = '$HOSTCHILL'
HOSTCACHE = '$HOSTCACHE'
HOSTORIGIN = '$HOSTORIGIN'
# The HOSTAPI should not be externally available.
# Keep HOSTAPI as localhost (127.0.0.1)
HOSTAPI = '$HOSTAPI'
HOSTPUBLISH = '$HOSTPUBLISH'
PORTAPI = $PORTAPI
PORTPUBLISH = $PORTPUBLISH

# The other app for divulging piece movements
HOSTDIVULGER = '$HOSTDIVULGER'
PORTDIVULGER = $PORTDIVULGER
HOSTSTREAM = '$HOSTSTREAM'
PORTSTREAM = $PORTSTREAM

HOSTREDIS = '$HOSTREDIS'
PORTREDIS = $PORTREDIS
# The redis db is by default 0 and the redis db used for unit tests is 1
REDIS_DB = $REDIS_DB
REDIS_URL = 'redis://${HOSTREDIS}:${PORTREDIS}/${REDIS_DB}/'

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
with open('package.json') as f:
    PACKAGEJSON = json.load(f)
    VERSION = PACKAGEJSON['version']
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

# Chill is set to use Flask-Cache by default.  Puzzle Massive is using a NGINX
# cache server, so disabling Flask-Cache here by setting cache type to null.
CACHE_NO_NULL_WARNING = True
CACHE_TYPE = "null"
#CACHE_TYPE = "simple"
#CACHE_TYPE = "filesystem"
#CACHE_DEFAULT_TIMEOUT = 50
#CACHE_THRESHOLD = 300
#CACHE_DIR = "${CACHEDIR}"

PURGEURLLIST = "${PURGEURLLIST}"

# https://pythonhosted.org/Frozen-Flask/#configuration
# For creating a stand-alone static website that you can upload without
# requiring an app to run it. This will use Frozen-Flask.
# The path to the static/frozen website will be put.
FREEZER_DESTINATION = "frozen"
FREEZER_BASE_URL = "{0}://{1}/".format(SITE_PROTOCOL, HOSTNAME)

# Unsplash
UNSPLASH_APPLICATION_ID = "${UNSPLASH_APPLICATION_ID}"
UNSPLASH_APPLICATION_NAME = "${UNSPLASH_APPLICATION_NAME}"
UNSPLASH_SECRET = "${UNSPLASH_SECRET}"

# Link to send images for suggested puzzles.  This could even be a
# "mailto:your-email@example.com", but I use a Dropbox file request link.
# Why bother?  The actual puzzle 'submit' form does handle image uploads, but
# I find it better to limit access to that form for new visitors.  This way
# there is less spam and I don't have to delete so many submitted puzzles that
# don't meet the criteria.  The suggest puzzle form doesn't create a puzzle like
# the submit puzzle form does.
# Leave this blank if the feature should be hidden.
SUGGEST_IMAGE_LINK = "${SUGGEST_IMAGE_LINK}"

SECURE_COOKIE_SECRET = "${SECURE_COOKIE_SECRET}"

# Either production or development
ENVIRONMENT="${ENVIRONMENT}"

# Temporary until the puzzle contributor role exists
NEW_PUZZLE_CONTRIB = "${NEW_PUZZLE_CONTRIB}"

# Email config
SMTP_HOST="${SMTP_HOST}"
SMTP_PORT="${SMTP_PORT}"
SMTP_USER="${SMTP_USER}"
SMTP_PASSWORD="${SMTP_PASSWORD}"
EMAIL_SENDER="${EMAIL_SENDER}"
EMAIL_MODERATOR="${EMAIL_MODERATOR}"

# The publish worker count is the number of workers that will handle piece
# movement requests. Set to None to be based on cpu count.
PUBLISH_WORKER_COUNT=${PUBLISH_WORKER_COUNT}

# The stream worker count is the number of workers that will handle connections
# to the stream. Set to None to be based on cpu count.
STREAM_WORKER_COUNT=${STREAM_WORKER_COUNT}

# Cache time to live for puzzle pieces requests. This value is in seconds.
PUZZLE_PIECES_CACHE_TTL = 20

# Puzzle settings
# The karma points shown to a player is the sum of recent_points and karma points.
# Recent points are per player
MAX_RECENT_POINTS = 25
RECENT_POINTS_EXPIRE = 1209600 # 14 days
# Karma points are per puzzle for the players on that network
INITIAL_KARMA = 10
MAX_KARMA = 25
KARMA_POINTS_EXPIRE = 3600  # hour in seconds
# Timeouts in seconds for each time a player gets blocked on a puzzle. These are
# network specific (IP address) and will reset (expire) on the last item in the
# list. For example, the first time a player gets down to 0 karma and gets
# blocked for a puzzle they will need to wait 30 seconds until being able to
# move pieces on that puzzle. The next time a player on that same network gets
# blocked on a puzzle they will need to wait 300 seconds. If no players on that
# network are blocked on a puzzle after the last timeout (3 days) the list is
# reset and the next player that gets blocked will again be for 30 seconds.
# The last item in this list should always be the longest.
BLOCKEDPLAYER_EXPIRE_TIMEOUTS = list(map(int,"${BLOCKEDPLAYER_EXPIRE_TIMEOUTS}".split()))
MINIMUM_PIECE_COUNT=${MINIMUM_PIECE_COUNT}
MAXIMUM_PIECE_COUNT=${MAXIMUM_PIECE_COUNT}

PUZZLE_PIECE_GROUPS = list(map(int,"${PUZZLE_PIECE_GROUPS}".split()))
ACTIVE_PUZZLES_IN_PIECE_GROUPS = list(map(int,"${ACTIVE_PUZZLES_IN_PIECE_GROUPS}".split()))
MINIMUM_IN_QUEUE_PUZZLES_IN_PIECE_GROUPS = list(map(int,"${MINIMUM_IN_QUEUE_PUZZLES_IN_PIECE_GROUPS}".split()))
SKILL_LEVEL_RANGES = list(zip([0] + PUZZLE_PIECE_GROUPS, PUZZLE_PIECE_GROUPS))

MAX_POINT_COST_FOR_REBUILDING=${MAX_POINT_COST_FOR_REBUILDING}
MAX_POINT_COST_FOR_DELETING=${MAX_POINT_COST_FOR_DELETING}
BID_COST_PER_PUZZLE=${BID_COST_PER_PUZZLE}
POINT_COST_FOR_CHANGING_BIT=${POINT_COST_FOR_CHANGING_BIT}
POINT_COST_FOR_CHANGING_NAME=${POINT_COST_FOR_CHANGING_NAME}
NEW_USER_STARTING_POINTS=${NEW_USER_STARTING_POINTS}
POINTS_CAP=${POINTS_CAP}
# New players that are still on a shareduser account will need to have at least
# this many points (dots) before they can claim their account.
MINIMUM_TO_CLAIM_ACCOUNT = NEW_USER_STARTING_POINTS + POINT_COST_FOR_CHANGING_BIT
# Bit icon expiration converted to an object
BIT_ICON_EXPIRATION = dict(map(lambda x: [int(x[:x.index(':')]), x[1 + x.index(':'):].strip()], """${BIT_ICON_EXPIRATION}""".split(',')))
# How many seconds to try to move a piece before it times out.
PIECE_MOVE_TIMEOUT = 4
# The player can pause piece movements on their end for this max time in seconds.
MAX_PAUSE_PIECES_TIMEOUT = 15
# The token lock timeout prevents other players from stealing pieces from the
# player that clicked on it first. The player has this much time to finish their
# piece movement before it can be taken from them by another player.
TOKEN_LOCK_TIMEOUT = 5
# Tokens that are used for piece movements are deleted after the piece has been
# moved. The token expire timeout is the max time that the token will be valid.
TOKEN_EXPIRE_TIMEOUT = 60 * 5
# Hide player bits on a puzzle after this many seconds of them not moving
# a piece.
PLAYER_BIT_RECENT_ACTIVITY_TIMEOUT = 10
# Tolerance in pixels that pieces need to be within when checking if they join.
# Set at 100 pixels for players with a touch device since the accuracy is around
# 50 pixels. 50 to the left + 50 to the right for example.
PIECE_JOIN_TOLERANCE = 100

AUTO_APPROVE_PUZZLES=True if "${AUTO_APPROVE_PUZZLES}".lower() == "y" else False

LOCAL_PUZZLE_RESOURCES=True if "${LOCAL_PUZZLE_RESOURCES}".lower() == "y" else False
CDN_BASE_URL = "${CDN_BASE_URL}"
PUZZLE_RESOURCES_BUCKET_REGION = "${PUZZLE_RESOURCES_BUCKET_REGION}"
PUZZLE_RESOURCES_BUCKET_ENDPOINT_URL = "${PUZZLE_RESOURCES_BUCKET_ENDPOINT_URL}"
PUZZLE_RESOURCES_BUCKET = "${PUZZLE_RESOURCES_BUCKET}"
PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL = "${PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL}"

# See PUZZLE_RULES_HELP_TEXT in bin/create_dot_env.sh
PUZZLE_RULES = set("${PUZZLE_RULES}".split())

# Enable puzzle features. Run python api/api/update_enabled_puzzle_features.py
# if this changes.
PUZZLE_FEATURES=set("${PUZZLE_FEATURES}".split())

# Toggle to show other player bit icons on the puzzle page.
SHOW_OTHER_PLAYER_BITS=True

DOMAIN_NAME = "${DOMAIN_NAME}"
SITE_TITLE = "${SITE_TITLE}"
HOME_PAGE_ROUTE = "${HOME_PAGE_ROUTE}"
SOURCE_CODE_LINK = "${SOURCE_CODE_LINK}"
M3="""${M3}"""

HERE
