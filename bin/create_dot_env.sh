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
# 'nginx_piece_publish_limit' to use piece move rate limits on nginx web server
"
read -e -p "${PUZZLE_RULES_HELP_TEXT}
" -i "${PUZZLE_RULES}" PUZZLE_RULES;

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

# These are mostly optional and self explanatory. Email settings are for
# transactional emails and currently only used when a photo for a puzzle is
# suggested. If hosting a production version of the site is planned, then set the
# domain name to something other then puzzle.massive.xyz. Leave it with the
# default if only doing local development on your own machine.
SUGGEST_IMAGE_LINK='https://any-website-for-uploading/'
SMTP_HOST='localhost'
SMTP_PORT='587'
SMTP_USER='user@localhost'
SMTP_PASSWORD='somepassword'
EMAIL_SENDER='sender@localhost'
EMAIL_MODERATOR='moderator@localhost'

${PUZZLE_RULES_HELP_TEXT}
PUZZLE_RULES="${PUZZLE_RULES}"

DOMAIN_NAME='puzzle.massive.xyz'
HERE
) > .env

echo "Created .env file with the below contents:"
echo ""
cat .env
echo ""
