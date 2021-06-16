#!/usr/bin/env bash

set -euo pipefail

CHECKOUT_COMMIT=$1
REPOSITORY_CLONE_URL=$2
ENV_FILE=$3
HTPASSWD_FILE=$4

cd /home/dev/

# TODO: AWS S3 CLI setup

# Get the source code
git clone $REPOSITORY_CLONE_URL puzzle-massive
cd puzzle-massive
git checkout $CHECKOUT_COMMIT

cp $ENV_FILE .env
cp $HTPASSWD_FILE .htpasswd

# Standard build stuff
su --command '
npm install;
npm run debug;
' dev

mkdir -p /usr/local/src/puzzle-massive;
chown dev:dev /usr/local/src/puzzle-massive;

# Sends files to the /usr/local/src/puzzle-massive directory
./bin/devsync.sh . /usr/local/src/puzzle-massive/
chown -R dev:dev /usr/local/src/puzzle-massive;

cd /usr/local/src/puzzle-massive;
su --command '
  python -m venv .;
  make;
' dev
make install;
./bin/appctl.sh stop -f;
su --command '
  ./bin/python api/api/create_database.py site.cfg;
  ./bin/python api/api/jobs/insert-or-replace-bit-icons.py;
  ./bin/python api/api/update_enabled_puzzle_features.py;
' dev
nginx -t;
systemctl reload nginx;
./bin/appctl.sh start;
./bin/appctl.sh status;
