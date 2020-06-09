#!/usr/bin/env bash
set -eu -o pipefail

SRCDIR=$1

DATE=$(date)

cat <<HERE

# File generated from $0
# on ${DATE}

[Unit]
Description=worker puzzle-massive instance
After=network.target
After=puzzle-massive-api.service

[Service]
User=dev
Group=dev
WorkingDirectory=$SRCDIR
ExecStart=${SRCDIR}bin/puzzle-massive-worker site.cfg serve

[Install]
WantedBy=multi-user.target

HERE
