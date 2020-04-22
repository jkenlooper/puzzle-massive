#!/usr/bin/env bash
set -eu -o pipefail

ENVIRONMENT=$1
SRCDIR=$2

DATE=$(date)

cat <<HERE

# File generated from $0
# on ${DATE}

[Unit]
Description=Puzzle Massive backup database
After=network.target

[Service]
User=dev
Group=dev
WorkingDirectory=$SRCDIR
HERE
if test "${ENVIRONMENT}" == 'development'; then
echo "ExecStart=${SRCDIR}bin/backup.sh -d /home/dev db-development.dump.gz"
else
echo "ExecStart=${SRCDIR}bin/backup.sh -d /home/dev -w"
fi
cat <<HERE

[Install]
WantedBy=multi-user.target

HERE
