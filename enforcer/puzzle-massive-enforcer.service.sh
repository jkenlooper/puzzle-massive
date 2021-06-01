#!/usr/bin/env bash
set -eu -o pipefail

SRCDIR=$1

DATE=$(date)

cat <<HERE

# File generated from $0
# on ${DATE}
# https://www.freedesktop.org/software/systemd/man/systemd.service.html

[Unit]
Description=Enforcer for Puzzle Massive
After=multi-user.target

[Service]
Type=exec
User=dev
Group=dev
WorkingDirectory=$SRCDIR
ExecStart=${SRCDIR}bin/puzzle-massive-enforcer start --config site.cfg
Restart=on-failure
# Restart every 13 hours in case of memory leaks or other issues
RuntimeMaxSec=46800

[Install]
WantedBy=multi-user.target

HERE
