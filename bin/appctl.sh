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
fi
systemctl reload nginx;

# Skipping the puzzle-massive-cache-purge.service since it is activated by path
# Skipping divulger and worker since they are not needed at the moment.
# puzzle-massive-divulger \
# puzzle-massive-worker \
# Skipping puzzle-massive-backup-db.timer to prevent database locks with
# scheduler. Backups should be done manually for now; see bin/reload.sh script.
# puzzle-massive-backup-db.timer \
for app in puzzle-massive-chill \
  puzzle-massive-api \
  puzzle-massive-stream \
  puzzle-massive-artist \
  puzzle-massive-scheduler \
  puzzle-massive-janitor;
do
  echo "";
  echo "systemctl $COMMAND $app;";
  echo "----------------------------------------";
  systemctl "$COMMAND" "$app" | cat;
done;
