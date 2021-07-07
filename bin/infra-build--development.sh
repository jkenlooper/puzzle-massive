#!/usr/bin/env bash

set -euo pipefail

ARTIFACT=$1
ENV_FILE=$2

cd /home/dev/

# Get the source code
git clone $ARTIFACT puzzle-massive
cd puzzle-massive

cp $ENV_FILE .env
chown -R dev:dev ../puzzle-massive

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
