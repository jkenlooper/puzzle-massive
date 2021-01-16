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

# The .env file has some environment variables that can be added if the app
# requires them. Uncomment this line as well as the EXAMPLE_PUBLIC_KEY below.
#source ".env"

HOST='127.0.0.1'
# The HOSTAPI should not be externally available.
# Keep HOSTAPI as localhost (127.0.0.1)
HOSTAPI='127.0.0.1'
# The HOSTPUBLISH should not be externally available.
# Keep HOSTPUBLISH as localhost (127.0.0.1)
HOSTPUBLISH='127.0.0.1'
HOSTDIVULGER='127.0.0.1'
HOSTSTREAM='127.0.0.1'
HOSTREDIS='127.0.0.1'
# The redis db is by default 0 and the redis db used for unit tests is 1
REDIS_DB=0

DATE=$(date)

if test "$ENVIRONMENT" == 'development'; then
  HOSTNAME="'local-puzzle-massive'"
  DEBUG=True
else
  HOSTNAME="'${DOMAIN_NAME}'"
  DEBUG=False
fi

cat <<HERE
# File generated from $0
# on ${DATE}

# The site.cfg file is used to configure a flask app.  Refer to the flask
# documentation for other configurations.  The below are used specifically by
# Chill.

# Set the HOST to 0.0.0.0 for being an externally visible server.
HOST = '127.0.0.1'
HOSTNAME = $HOSTNAME
SITE_PROTOCOL = 'http'
PORT = $PORTCHILL

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

# Temporary until the puzzle contributor role exists
NEW_PUZZLE_CONTRIB = "${NEW_PUZZLE_CONTRIB}"

# Email config
SMTP_HOST="${SMTP_HOST}"
SMTP_PORT="${SMTP_PORT}"
SMTP_USER="${SMTP_USER}"
SMTP_PASSWORD="${SMTP_PASSWORD}"
EMAIL_SENDER="${EMAIL_SENDER}"
EMAIL_MODERATOR="${EMAIL_MODERATOR}"

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
BLOCKEDPLAYER_EXPIRE_TIMEOUTS = [
    30,             # 30 seconds
    300,            # 5 minutes
    3600,           # 1 hour
    3600 * 3,       # 3 hours
    3600 * 24,      # 1 day
    3600 * 24 * 3,  # 3 days
]
MINIMUM_PIECE_COUNT = 20
MAX_POINT_COST_FOR_REBUILDING = 1000
MAX_POINT_COST_FOR_DELETING = 1000
BID_COST_PER_PUZZLE = 100
POINT_COST_FOR_CHANGING_BIT = 100
POINT_COST_FOR_CHANGING_NAME = 100
NEW_USER_STARTING_POINTS = 1300
POINTS_CAP = 15000
# How many seconds to try to move a piece before it times out.
PIECE_MOVE_TIMEOUT = 4
# The player can pause piece movements on their end for this max time in seconds.
MAX_PAUSE_PIECES_TIMEOUT = 15
# Tolerance in pixels that pieces need to be within when checking if they join.
# Set at 100 pixels for players with a touch device since the accuracy is around
# 50 pixels. 50 to the left + 50 to the right for example.
PIECE_JOIN_TOLERANCE = 100

# See PUZZLE_RULES_HELP_TEXT in bin/create_dot_env.sh
PUZZLE_RULES = set("${PUZZLE_RULES}".split(" "))

DOMAIN_NAME = "${DOMAIN_NAME}"
M3="""<img src="data:,PHAgc3R5bGU9ImNvbG9yOnRyYW5zcGFyZW50O2N1cnNvcjpkZWZhdWx0O3BvaW50ZXItZXZlbnRzOm5vbmU7cG9zaXRpb246YWJzb2x1dGU7bWFyZ2luOjA7cGFkZGluZzowO2hlaWdodDowOyI+PG1hcnF1ZWU+PHNtYWxsPlNjZW5lIDMgQVJUSFVSOiBPbGQgd29tYW4hIERFTk5JUzogTWFuISBBUlRIVVI6IE9sZCBNYW4sIHNvcnJ5LiBXaGF0IGtuaWdodCBsaXZlIGluIHRoYXQgY2FzdGxlIG92ZXIgdGhlcmU/IERFTk5JUzogSSdtIHRoaXJ0eSBzZXZlbi4gQVJUSFVSOiBXaGF0PyBERU5OSVM6IEknbSB0aGlydHkgc2V2ZW4gLS0gSSdtIG5vdCBvbGQhIEFSVEhVUjogV2VsbCwgSSBjYW4ndCBqdXN0IGNhbGwgeW91ICdNYW4nLiBERU5OSVM6IFdlbGwsIHlvdSBjb3VsZCBzYXkgJ0Rlbm5pcycuIEFSVEhVUjogV2VsbCwgSSBkaWRuJ3Qga25vdyB5b3Ugd2VyZSBjYWxsZWQgJ0Rlbm5pcy4nIERFTk5JUzogV2VsbCwgeW91IGRpZG4ndCBib3RoZXIgdG8gZmluZCBvdXQsIGRpZCB5b3U/IEFSVEhVUjogSSBkaWQgc2F5IHNvcnJ5IGFib3V0IHRoZSAnb2xkIHdvbWFuLCcgYnV0IGZyb20gdGhlIGJlaGluZCB5b3UgbG9va2VkLS0gREVOTklTOiBXaGF0IEkgb2JqZWN0IHRvIGlzIHlvdSBhdXRvbWF0aWNhbGx5IHRyZWF0IG1lIGxpa2UgYW4gaW5mZXJpb3IhIEFSVEhVUjogV2VsbCwgSSBBTSBraW5nLi4uIERFTk5JUzogT2gga2luZywgZWgsIHZlcnkgbmljZS4gQW4nIGhvdydkIHlvdSBnZXQgdGhhdCwgZWg/IEJ5IGV4cGxvaXRpbicgdGhlIHdvcmtlcnMgLS0gYnkgJ2FuZ2luJyBvbiB0byBvdXRkYXRlZCBpbXBlcmlhbGlzdCBkb2dtYSB3aGljaCBwZXJwZXR1YXRlcyB0aGUgZWNvbm9taWMgYW4nIHNvY2lhbCBkaWZmZXJlbmNlcyBpbiBvdXIgc29jaWV0eSEgSWYgdGhlcmUncyBldmVyIGdvaW5nIHRvIGJlIGFueSBwcm9ncmVzcy0tIFdPTUFOOiBEZW5uaXMsIHRoZXJlJ3Mgc29tZSBsb3ZlbHkgZmlsdGggZG93biBoZXJlLiBPaCAtLSBob3cgZCd5b3UgZG8/IEFSVEhVUjogSG93IGRvIHlvdSBkbywgZ29vZCBsYWR5LiBJIGFtIEFydGh1ciwgS2luZyBvZiB0aGUgQnJpdG9ucy4gV2hvJ3MgY2FzdGxlIGlzIHRoYXQ/IFdPTUFOOiBLaW5nIG9mIHRoZSB3aG8/IEFSVEhVUjogVGhlIEJyaXRvbnMuIFdPTUFOOiBXaG8gYXJlIHRoZSBCcml0b25zPyBBUlRIVVI6IFdlbGwsIHdlIGFsbCBhcmUuIHdlJ3JlIGFsbCBCcml0b25zIGFuZCBJIGFtIHlvdXIga2luZy4gV09NQU46IEkgZGlkbid0IGtub3cgd2UgaGFkIGEga2luZy4gSSB0aG91Z2h0IHdlIHdlcmUgYW4gYXV0b25vbW91cyBjb2xsZWN0aXZlLiBERU5OSVM6IFlvdSdyZSBmb29saW5nIHlvdXJzZWxmLiBXZSdyZSBsaXZpbmcgaW4gYSBkaWN0YXRvcnNoaXAuIEEgc2VsZi1wZXJwZXR1YXRpbmcgYXV0b2NyYWN5IGluIHdoaWNoIHRoZSB3b3JraW5nIGNsYXNzZXMtLSBXT01BTjogT2ggdGhlcmUgeW91IGdvLCBicmluZ2luZyBjbGFzcyBpbnRvIGl0IGFnYWluLiBERU5OSVM6IFRoYXQncyB3aGF0IGl0J3MgYWxsIGFib3V0IGlmIG9ubHkgcGVvcGxlIHdvdWxkLS0gQVJUSFVSOiBQbGVhc2UsIHBsZWFzZSBnb29kIHBlb3BsZS4gSSBhbSBpbiBoYXN0ZS4gV2hvIGxpdmVzIGluIHRoYXQgY2FzdGxlPyBXT01BTjogTm8gb25lIGxpdmUgdGhlcmUuIEFSVEhVUjogVGhlbiB3aG8gaXMgeW91ciBsb3JkPyBXT01BTjogV2UgZG9uJ3QgaGF2ZSBhIGxvcmQuIEFSVEhVUjogV2hhdD8gREVOTklTOiBJIHRvbGQgeW91LiBXZSdyZSBhbiBhbmFyY2hvLXN5bmRpY2FsaXN0IGNvbW11bmUuIFdlIHRha2UgaXQgaW4gdHVybnMgdG8gYWN0IGFzIGEgc29ydCBvZiBleGVjdXRpdmUgb2ZmaWNlciBmb3IgdGhlIHdlZWsuIEFSVEhVUjogWWVzLiBERU5OSVM6IEJ1dCBhbGwgdGhlIGRlY2lzaW9uIG9mIHRoYXQgb2ZmaWNlciBoYXZlIHRvIGJlIHJhdGlmaWVkIGF0IGEgc3BlY2lhbCBiaXdlZWtseSBtZWV0aW5nLiBBUlRIVVI6IFllcywgSSBzZWUuIERFTk5JUzogQnkgYSBzaW1wbGUgbWFqb3JpdHkgaW4gdGhlIGNhc2Ugb2YgcHVyZWx5IGludGVybmFsIGFmZmFpcnMsLS0gQVJUSFVSOiBCZSBxdWlldCEgREVOTklTOiAtLWJ1dCBieSBhIHR3by10aGlyZHMgbWFqb3JpdHkgaW4gdGhlIGNhc2Ugb2YgbW9yZS0tIEFSVEhVUjogQmUgcXVpZXQhIEkgb3JkZXIgeW91IHRvIGJlIHF1aWV0ISBXT01BTjogT3JkZXIsIGVoIC0tIHdobyBkb2VzIGhlIHRoaW5rIGhlIGlzPyBBUlRIVVI6IEkgYW0geW91ciBraW5nISBXT01BTjogV2VsbCwgSSBkaWRuJ3Qgdm90ZSBmb3IgeW91LiBBUlRIVVI6IFlvdSBkb24ndCB2b3RlIGZvciBraW5ncy4gV09NQU46IFdlbGwsICdvdyBkaWQgeW91IGJlY29tZSBraW5nIHRoZW4/IEFSVEhVUjogVGhlIExhZHkgb2YgdGhlIExha2UsIFthbmdlbHMgc2luZ10gaGVyIGFybSBjbGFkIGluIHRoZSBwdXJlc3Qgc2hpbW1lcmluZyBzYW1pdGUsIGhlbGQgYWxvZnQgRXhjYWxpYnVyIGZyb20gdGhlIGJvc29tIG9mIHRoZSB3YXRlciBzaWduaWZ5aW5nIGJ5IERpdmluZSBQcm92aWRlbmNlIHRoYXQgSSwgQXJ0aHVyLCB3YXMgdG8gY2FycnkgRXhjYWxpYnVyLiBbc2luZ2luZyBzdG9wc10gVGhhdCBpcyB3aHkgSSBhbSB5b3VyIGtpbmchIERFTk5JUzogTGlzdGVuIC0tIHN0cmFuZ2Ugd29tZW4gbHlpbmcgaW4gcG9uZHMgZGlzdHJpYnV0aW5nIHN3b3JkcyBpcyBubyBiYXNpcyBmb3IgYSBzeXN0ZW0gb2YgZ292ZXJubWVudC4gU3VwcmVtZSBleGVjdXRpdmUgcG93ZXIgZGVyaXZlcyBmcm9tIGEgbWFuZGF0ZSBmcm9tIHRoZSBtYXNzZXMsIG5vdCBmcm9tIHNvbWUgZmFyY2ljYWwgYXF1YXRpYyBjZXJlbW9ueS4gQVJUSFVSOiBCZSBxdWlldCEgREVOTklTOiBXZWxsIHlvdSBjYW4ndCBleHBlY3QgdG8gd2llbGQgc3VwcmVtZSBleGVjdXRpdmUgcG93ZXIganVzdCAnY2F1c2Ugc29tZSB3YXRlcnkgdGFydCB0aHJldyBhIHN3b3JkIGF0IHlvdSEgQVJUSFVSOiBTaHV0IHVwISBERU5OSVM6IEkgbWVhbiwgaWYgSSB3ZW50IGFyb3VuZCBzYXlpbicgSSB3YXMgYW4gZW1wZXJlcm9yIGp1c3QgYmVjYXVzZSBzb21lIG1vaXN0ZW5lZCBiaW50IGhhZCBsb2JiZWQgYSBzY2ltaXRhciBhdCBtZSB0aGV5J2QgcHV0IG1lIGF3YXkhIEFSVEhVUjogU2h1dCB1cCEgV2lsbCB5b3Ugc2h1dCB1cCEgREVOTklTOiBBaCwgbm93IHdlIHNlZSB0aGUgdmlvbGVuY2UgaW5oZXJlbnQgaW4gdGhlIHN5c3RlbS4gQVJUSFVSOiBTaHV0IHVwISBERU5OSVM6IE9oISBDb21lIGFuZCBzZWUgdGhlIHZpb2xlbmNlIGluaGVyZW50IGluIHRoZSBzeXN0ZW0hIEhFTFAhIEhFTFAhIEknbSBiZWluZyByZXByZXNzZWQhIEFSVEhVUjogQmxvb2R5IHBlYXNhbnQhIERFTk5JUzogT2gsIHdoYXQgYSBnaXZlIGF3YXkuIERpZCB5b3UgaGVyZSB0aGF0LCBkaWQgeW91IGhlcmUgdGhhdCwgZWg/IFRoYXQncyB3aGF0IEknbSBvbiBhYm91dCAtLSBkaWQgeW91IHNlZSBoaW0gcmVwcmVzc2luZyBtZSwgeW91IHNhdyBpdCBkaWRuJ3QgeW91Pzwvc21hbGw+PC9tYXJxdWVlPjwvcD4=" onerror="this.outerHTML=atob(this.src.substr(this.src.indexOf(',')+1))">"""

HERE
