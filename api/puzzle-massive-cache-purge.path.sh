#!/usr/bin/env bash
set -eu -o pipefail

PURGEURLLIST=$1

DATE=$(date)

cat <<HERE

# File generated from $0
# on ${DATE}

[Unit]
Description=Activate the service if the purge url list file changes.
Wants=puzzle-massive-cache-purge.service

[Path]
PathExists=${PURGEURLLIST}
PathModified=${PURGEURLLIST}

[Install]
WantedBy=multi-user.target

HERE
