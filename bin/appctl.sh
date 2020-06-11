#!/usr/bin/env bash
set -eu -o pipefail

COMMAND=$1

# Simple convenience script to control the apps.

# Switch out nginx puzzle-massive.conf to puzzle-massive--down.conf to
# show the down page.
if test "${COMMAND}" == 'start'; then
    rm -f /etc/nginx/sites-enabled/puzzle-massive--down.conf;
    ln -sf /etc/nginx/sites-available/puzzle-massive.conf /etc/nginx/sites-enabled/puzzle-massive.conf;
elif test "${COMMAND}" == 'stop'; then
    rm -f /etc/nginx/sites-enabled/puzzle-massive.conf;
    ln -sf /etc/nginx/sites-available/puzzle-massive--down.conf /etc/nginx/sites-enabled/puzzle-massive--down.conf;
    # Stop the stream first before other apps.
    echo "Waiting for the puzzle-massive-stream connections...";
    systemctl stop puzzle-massive-stream;
fi
systemctl reload nginx;
if test "${COMMAND}" == 'stop'; then
    # Now that the app isn't accepting any outside requests; transfer piece data
    # to SQL database from redis database.
    su dev -c "source bin/activate; python api/api/jobs/convertPiecesToDB.py;"
fi

# Skipping the puzzle-massive-cache-purge.service since it is activated by path
# Skipping divulger and worker since they are not needed at the moment.
# puzzle-massive-divulger \
# puzzle-massive-worker \
for app in puzzle-massive-chill \
  puzzle-massive-api \
  puzzle-massive-stream \
  puzzle-massive-artist \
  puzzle-massive-scheduler \
  puzzle-massive-backup-db.timer \
  puzzle-massive-janitor;
do
  echo "";
  echo "systemctl $COMMAND $app;";
  echo "----------------------------------------";
  systemctl "$COMMAND" "$app" | cat;
done;
