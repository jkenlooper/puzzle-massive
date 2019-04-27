#!/usr/bin/env bash
set -eu -o pipefail

SRCDIR=$1

DATE=$(date)

cat <<HERE

# File generated from $0
# on ${DATE}

[Unit]
Description=scheduler puzzle-massive instance
After=network.target

[Service]
User=dev
Group=dev
WorkingDirectory=$SRCDIR
ExecStart=${SRCDIR}bin/puzzle-massive-scheduler site.cfg

[Install]
WantedBy=multi-user.target

HERE
