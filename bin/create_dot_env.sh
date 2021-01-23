#!/usr/bin/env bash
set -euo pipefail

function usage {
  cat <<USAGE
Usage: ${0} [-h]

Options:
  -h            Show help

Creates the .env and .htpasswd files used for Puzzle Massive development.
Existing files will be renamed with a .bak suffix.
USAGE
  exit 0;
}

while getopts ":h" opt; do
  case ${opt} in
    h )
      usage;
      ;;
    \? )
      usage;
      ;;
  esac;
done;
shift "$((OPTIND-1))";

# Defaults
SECURE_COOKIE_SECRET="chocolate chip"
MUPPET_CHARACTER="rizzo"
PUZZLE_RULES="all"
UNSPLASH_APPLICATION_ID=""
UNSPLASH_APPLICATION_NAME=""
UNSPLASH_SECRET=""
DOMAIN_NAME='puzzle.massive.xyz'
SUGGEST_IMAGE_LINK='https://any-website-for-uploading/'
SMTP_HOST='localhost'
SMTP_PORT='587'
SMTP_USER='user@localhost'
SMTP_PASSWORD='somepassword'
EMAIL_SENDER='sender@localhost'
EMAIL_MODERATOR='moderator@localhost'
PUBLISH_WORKER_COUNT=2
STREAM_WORKER_COUNT=2
BLOCKEDPLAYER_EXPIRE_TIMEOUTS='30 300 3600'
MINIMUM_PIECE_COUNT=20
MAXIMUM_PIECE_COUNT=50000
MAX_POINT_COST_FOR_REBUILDING=1000
MAX_POINT_COST_FOR_DELETING=1000
BID_COST_PER_PUZZLE=100
POINT_COST_FOR_CHANGING_BIT=100
POINT_COST_FOR_CHANGING_NAME=100
NEW_USER_STARTING_POINTS=1300
POINTS_CAP=15000
M3=''

if [ -f .env ]; then
  source .env
  mv --backup=numbered .env .env.bak
fi

read -e -p "
Enter some random text for secure cookie:

" -i "${SECURE_COOKIE_SECRET}" SECURE_COOKIE_SECRET;

read -e -p "
What is your favorite muppet character (should be one word):

" -i "${MUPPET_CHARACTER}" MUPPET_CHARACTER;

PUZZLE_RULES_HELP_TEXT="
# Enable rules to prevent players from messing up puzzles for others. These
# rules limit stacking pieces, moving lots of pieces at once, moving pieces to
# the same area, validating the token, etc..
# Set to 'all' to enable all rules
# Leave blank to disable all rules
# Or add only some rules (separate each with a space and no quotes):
# 'valid_token' to validate token for piece moves
# 'piece_translate_rate' to limit piece move rate per user
# 'max_stack_pieces' to limit how many pieces can be stacked
# 'stack_pieces' to limit joining pieces when stacked
# 'karma_stacked' decrease karma when stacking pieces
# 'karma_piece_group_move_max' decrease karma when moving large groups of pieces
# 'puzzle_open_rate' to limit how many puzzles can be opened within an hour
# 'piece_move_rate' to limit how many pieces can be moved within a minute or so
# 'hot_piece' to limit moving the same piece again within a minute or so
# 'hot_spot' to limit moving pieces to the same area within 30 seconds
# 'too_active' decrease karma on piece move when server responds with 503 error
# 'nginx_piece_publish_limit' to use piece move rate limits on nginx web server
"
read -e -p "${PUZZLE_RULES_HELP_TEXT}
" -i "${PUZZLE_RULES}" PUZZLE_RULES;

BLOCKEDPLAYER_EXPIRE_TIMEOUTS_HELP_TEXT="
# Timeouts in seconds for each time a player gets blocked on a puzzle. These are
# network specific (IP address) and will reset (expire) on the last item in the
# space separated list. For example, the first time a player gets down to
# 0 karma and gets blocked for a puzzle they will need to wait 30 seconds until
# being able to move pieces on that puzzle. The next time a player on that same
# network gets blocked on a puzzle they will need to wait 300 seconds. If no
# players on that network are blocked on a puzzle after the last timeout (3600
# seconds is one hour) the list is reset and the next player that gets blocked
# will again be for 30 seconds.  The last item in this list should always be the
# longest.
"
echo "${BLOCKEDPLAYER_EXPIRE_TIMEOUTS_HELP_TEXT}"
read -e -p "Blocked player expire timeouts:
" -i "${BLOCKEDPLAYER_EXPIRE_TIMEOUTS}" BLOCKEDPLAYER_EXPIRE_TIMEOUTS;

read -e -p "Minimum piece count:
" -i "${MINIMUM_PIECE_COUNT}" MINIMUM_PIECE_COUNT;

read -e -p "Maximum piece count:
" -i "${MAXIMUM_PIECE_COUNT}" MAXIMUM_PIECE_COUNT;

read -e -p "Max point cost for rebuilding:
" -i "${MAX_POINT_COST_FOR_REBUILDING}" MAX_POINT_COST_FOR_REBUILDING;

read -e -p "Max point cost for deleting:
" -i "${MAX_POINT_COST_FOR_DELETING}" MAX_POINT_COST_FOR_DELETING;

read -e -p "Bid cost per puzzle:
" -i "${BID_COST_PER_PUZZLE}" BID_COST_PER_PUZZLE;

read -e -p "Point cost for changing bit:
" -i "${POINT_COST_FOR_CHANGING_BIT}" POINT_COST_FOR_CHANGING_BIT;

read -e -p "Point cost for changing name:
" -i "${POINT_COST_FOR_CHANGING_NAME}" POINT_COST_FOR_CHANGING_NAME;

read -e -p "New user starting points:
" -i "${NEW_USER_STARTING_POINTS}" NEW_USER_STARTING_POINTS;

read -e -p "Points cap:
" -i "${POINTS_CAP}" POINTS_CAP;

UNSPLASH_HELP_TEXT="
# It is recommended to set up an account on [Unsplash](https://unsplash.com/). An
# app will need to be created in order to get the application id and such. See
# [Unsplash Image API](https://unsplash.com/developers).
# Leave these blank if not using images from Unsplash.
"
echo "${UNSPLASH_HELP_TEXT}"
read -e -p "Unsplash application ID:
" -i "${UNSPLASH_APPLICATION_ID}" UNSPLASH_APPLICATION_ID;
read -e -p "Unsplash application name:
" -i "${UNSPLASH_APPLICATION_NAME}" UNSPLASH_APPLICATION_NAME;
read -e -p "Unsplash secret:
" -i "${UNSPLASH_SECRET}" UNSPLASH_SECRET;

echo "
The domain name here is only used if deploying to a server. It can be set
to whatever for local development."
read -e -p "Domain name to use for the puzzle website:
" -i "${DOMAIN_NAME}" DOMAIN_NAME;

read -e -p "Suggest image link:
" -i "${SUGGEST_IMAGE_LINK}" SUGGEST_IMAGE_LINK;

EMAIL_SETTINGS_HELP_TEXT="
# Email settings are for transactional emails and are used when a photo for
# a puzzle is suggested.  Emails are also used for verifying a player's account
# email so they can reset their login. Leave these blank to disable those
# features.
"
read -e -p "smtp host:
" -i "${SMTP_HOST}" SMTP_HOST;
read -e -p "smtp port:
" -i "${SMTP_PORT}" SMTP_PORT;
read -e -p "smtp user:
" -i "${SMTP_USER}" SMTP_USER;
read -e -p "smtp password:
" -i "${SMTP_PASSWORD}" SMTP_PASSWORD;
read -e -p "email sender:
" -i "${EMAIL_SENDER}" EMAIL_SENDER;
read -e -p "email moderator:
" -i "${EMAIL_MODERATOR}" EMAIL_MODERATOR;

PUBLISH_WORKER_COUNT_HELP_TEXT="
# The publish worker count is the number of workers that will handle piece
# movement requests. Set to None to be based on cpu count.
"
echo "${PUBLISH_WORKER_COUNT_HELP_TEXT}"
read -e -p "publish worker count:
" -i "${PUBLISH_WORKER_COUNT}" PUBLISH_WORKER_COUNT;

STREAM_WORKER_COUNT_HELP_TEXT="
# The stream worker count is the number of workers that will handle connections
# to the stream. Set to None to be based on cpu count.
"
echo "${STREAM_WORKER_COUNT_HELP_TEXT}"
read -e -p "publish worker count:
" -i "${STREAM_WORKER_COUNT}" STREAM_WORKER_COUNT;


(
cat <<HERE

${UNSPLASH_HELP_TEXT}
UNSPLASH_APPLICATION_ID='${UNSPLASH_APPLICATION_ID}'
UNSPLASH_APPLICATION_NAME='${UNSPLASH_APPLICATION_NAME}'
UNSPLASH_SECRET='${UNSPLASH_SECRET}'

# Set these to something unique for the app. The NEW_PUZZLE_CONTRIB sets the URL
# used for directly submitting photos for puzzles. Eventually the puzzle
# contributor stuff will be done, but for now set it to your favorite
# [Muppet character](https://en.wikipedia.org/wiki/List_of_Muppets).
NEW_PUZZLE_CONTRIB='${MUPPET_CHARACTER}'
SECURE_COOKIE_SECRET='${SECURE_COOKIE_SECRET}'

SUGGEST_IMAGE_LINK='${SUGGEST_IMAGE_LINK}'

${EMAIL_SETTINGS_HELP_TEXT}
SMTP_HOST='${SMTP_HOST}'
SMTP_PORT='${SMTP_PORT}'
SMTP_USER='${SMTP_USER}'
SMTP_PASSWORD='${SMTP_PASSWORD}'
EMAIL_SENDER='${EMAIL_SENDER}'
EMAIL_MODERATOR='${EMAIL_MODERATOR}'

${PUZZLE_RULES_HELP_TEXT}
PUZZLE_RULES="${PUZZLE_RULES}"

${BLOCKEDPLAYER_EXPIRE_TIMEOUTS_HELP_TEXT}
BLOCKEDPLAYER_EXPIRE_TIMEOUTS="${BLOCKEDPLAYER_EXPIRE_TIMEOUTS}"

MINIMUM_PIECE_COUNT=${MINIMUM_PIECE_COUNT}
MAXIMUM_PIECE_COUNT=${MAXIMUM_PIECE_COUNT}

MAX_POINT_COST_FOR_REBUILDING=${MAX_POINT_COST_FOR_REBUILDING}
MAX_POINT_COST_FOR_DELETING=${MAX_POINT_COST_FOR_DELETING}
BID_COST_PER_PUZZLE=${BID_COST_PER_PUZZLE}
POINT_COST_FOR_CHANGING_BIT=${POINT_COST_FOR_CHANGING_BIT}
POINT_COST_FOR_CHANGING_NAME=${POINT_COST_FOR_CHANGING_NAME}
NEW_USER_STARTING_POINTS=${NEW_USER_STARTING_POINTS}
POINTS_CAP=${POINTS_CAP}

${PUBLISH_WORKER_COUNT_HELP_TEXT}
PUBLISH_WORKER_COUNT=${PUBLISH_WORKER_COUNT}

${STREAM_WORKER_COUNT_HELP_TEXT}
STREAM_WORKER_COUNT=${STREAM_WORKER_COUNT}

DOMAIN_NAME="${DOMAIN_NAME}"
M3="${M3}"
HERE
) > .env

echo "Created .env file with the below contents:"
echo ""
cat .env
echo ""
