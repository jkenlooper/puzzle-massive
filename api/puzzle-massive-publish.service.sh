#!/usr/bin/env bash
set -eu -o pipefail

ENVIRONMENT=$1
SRCDIR=$2

DATE=$(date)

cat <<HERE

# File generated from $0
# on ${DATE}
# https://www.freedesktop.org/software/systemd/man/systemd.service.html

[Unit]
Description=Publish puzzle-massive instance
After=multi-user.target

[Service]
Type=exec
User=dev
Group=dev
WorkingDirectory=$SRCDIR
HERE
if test "${ENVIRONMENT}" == 'development'; then
echo "ExecStart=${SRCDIR}bin/puzzle-massive-publish serve"
else
echo "ExecStart=${SRCDIR}bin/puzzle-massive-publish serve"
fi
cat <<HERE
Restart=on-failure

[Install]
WantedBy=multi-user.target

HERE
