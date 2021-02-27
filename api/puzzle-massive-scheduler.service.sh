#!/usr/bin/env bash
set -eu -o pipefail

SRCDIR=$1

DATE=$(date)

cat <<HERE

# File generated from $0
# on ${DATE}
# https://www.freedesktop.org/software/systemd/man/systemd.service.html

[Unit]
Description=scheduler puzzle-massive instance
After=multi-user.target

[Service]
Type=exec
User=dev
Group=dev
WorkingDirectory=$SRCDIR
ExecStart=${SRCDIR}bin/puzzle-massive-scheduler
Restart=on-failure

[Install]
WantedBy=multi-user.target

HERE
