#!/usr/bin/env bash
# not setting the -e or the option -o pipefail here. That way if a service fails
# to stop the others will continue to stop.

COMMAND=$1

SKIP_BACKUP=0
if [ -n "${2-}" ]; then
SKIP_BACKUP=$2
fi

# Simple convenience script to control the apps.

# Switch out nginx legacy-cache--up.nginx.conf to legacy-cache--down.nginx.conf to
# show the down page.
if test "${COMMAND}" == 'start'; then
    rm -f /etc/nginx/sites-enabled/legacy-cache--down.nginx.conf;
    ln -sf /etc/nginx/sites-available/legacy-cache--up.nginx.conf /etc/nginx/sites-enabled/legacy-cache--up.nginx.conf;
    # Start the puzzle-massive-api first since other services depend on it.
    systemctl start puzzle-massive-api;
    systemctl start puzzle-massive-stream;
    systemctl start puzzle-massive-enforcer;
    systemctl start puzzle-massive-publish;
    systemctl start puzzle-massive-scheduler;
    systemctl start puzzle-massive-chill;
    systemctl start puzzle-massive-janitor;
    systemctl start puzzle-massive-artist;
    systemctl start puzzle-massive-backup-db.timer;
    systemctl reload nginx;

elif test "${COMMAND}" == 'stop'; then
    rm -f /etc/nginx/sites-enabled/legacy-cache--up.nginx.conf;
    ln -sf /etc/nginx/sites-available/legacy-cache--down.nginx.conf /etc/nginx/sites-enabled/legacy-cache--down.nginx.conf;
    systemctl stop puzzle-massive-artist;
    systemctl stop puzzle-massive-chill;
    systemctl stop puzzle-massive-publish;
    systemctl stop puzzle-massive-scheduler;
    systemctl stop puzzle-massive-backup-db.timer;
    systemctl stop puzzle-massive-janitor;
    echo "Waiting for the puzzle-massive-stream connections...";
    systemctl stop puzzle-massive-stream;
    if [ "$SKIP_BACKUP" != "-f" ]; then
      su dev -c "bin/backup.sh -d /home/dev -c" || echo "Creating backup failed. Continuing to stop the other services."
    fi
    # Stop the puzzle-massive-api last since other services depend on it.
    systemctl stop puzzle-massive-api;
    systemctl stop puzzle-massive-enforcer;
    systemctl reload nginx;

else
  tmpout=$(mktemp)
  for app in puzzle-massive-chill \
    puzzle-massive-api \
    puzzle-massive-publish \
    puzzle-massive-stream \
    puzzle-massive-enforcer \
    puzzle-massive-artist \
    puzzle-massive-scheduler \
    puzzle-massive-backup-db.timer \
    puzzle-massive-janitor;
  do
    echo "";
    echo "systemctl $COMMAND $app;";
    echo "----------------------------------------";
    # Collect any error codes that may occur
    systemctl "$COMMAND" "$app" || echo "$app $?" >> $tmpout
  done;
  if [ -s $tmpout ]; then
    # Only output the error codes for each app if any happened.
    cat $tmpout
    exit 1
  fi
  rm -f $tmpout
fi
