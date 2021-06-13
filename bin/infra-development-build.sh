#!/usr/bin/env bash

set -euo pipefail

CHECKOUT_COMMIT=$1
REPOSITORY_CLONE_URL=$2
ENV_FILE=$3
HTPASSWD_FILE=$4

cd /home/dev/

echo "127.0.0.1 local-puzzle-massive" >> /etc/hosts
# The devsync.sh will use ssh to copy files to local-puzzle-massive.  Need to
# add that to the known hosts first.
su --command 'ssh-keyscan -H local-puzzle-massive >> /home/dev/.ssh/known_hosts' dev

# Get the source code
git clone $REPOSITORY_CLONE_URL puzzle-massive
cd puzzle-massive
git checkout $CHECKOUT_COMMIT

cp $ENV_FILE .env
cp $HTPASSWD_FILE .htpasswd

# Standard build stuff
npm install
npm run debug

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
