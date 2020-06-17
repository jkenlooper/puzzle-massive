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


which htpasswd > /dev/null || (echo "No htpasswd command found. Install apache2-utils to get htpasswd command." && exit 1)

which rsync > /dev/null || (echo "No rsync command found. Install rsync." && exit 1)

read -p "Enter some random text for secure cookie: " SECURE_COOKIE_SECRET;
read -p "What is your favorite muppet character (should be one word): " MUPPET_CHARACTER;
echo ""

if [ -f .env ]; then
  mv --backup=numbered .env .env.bak
fi

(
cat <<HERE

# It is recommended to set up an account on [Unsplash](https://unsplash.com/). An
# app will need to be created in order to get the application id and such. See
# [Unsplash Image API](https://unsplash.com/developers). Leave blank if not using
# images from Unsplash.
UNSPLASH_APPLICATION_ID=
UNSPLASH_APPLICATION_NAME=
UNSPLASH_SECRET=

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
DOMAIN_NAME='puzzle.massive.xyz'
HERE
) > .env

echo "Created .env file with the below contents:"
echo ""
cat .env
echo ""

cat <<HERE
The admin page uses basic auth. Note that this site does not default to use
a secure protocol (https) and so anyone on your network _could_ see the password
used here. Not really a big deal, but for production deployments the nginx
config is also set to deny any requests to the admin page if not originating
from the internal IP. Admin page access for production requires using a proxy
or changing the nginx config.
HERE

# Set the initial admin user and password. This file is copied to the
# /srv/puzzle-massive/ when installing with `make install`.
if [ -f .htpasswd ]; then
  mv --backup=numbered .htpasswd .htpasswd.bak
fi
echo "Enter password for new .htpasswd file."
htpasswd -c .htpasswd $(whoami);
