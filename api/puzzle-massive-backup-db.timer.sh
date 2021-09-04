#!/usr/bin/env bash
set -eu -o pipefail

ENVIRONMENT=$1

DATE=$(date)

cat <<HERE

# File generated from $0
# on ${DATE}
# https://www.freedesktop.org/software/systemd/man/systemd.service.html

[Unit]
Description=Run puzzle-massive-backup-db every 13 hours
Requires=puzzle-massive-backup-db.service

[Timer]
Unit=puzzle-massive-backup-db.service
# TODO: OnActiveSec?
OnActiveSec=1min
HERE
if test "${ENVIRONMENT}" == 'development'; then
echo "OnUnitActiveSec=1hour"
else
echo "OnUnitActiveSec=13hours"
fi
cat <<HERE

[Install]
WantedBy=timers.target

HERE
