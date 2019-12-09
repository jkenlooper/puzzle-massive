#!/usr/bin/env bash
set -eu -o pipefail

PORTREGISTRY=$1
CACHEDIR=$2
SRCDIR=$3
PURGEURLLIST=$4

# shellcheck source=/dev/null
source "$PORTREGISTRY"

DATE=$(date)

origin_server=http://localhost:${PORTORIGIN}

cat <<HERE

# File generated from $0
# on ${DATE}

[Unit]
Description=Purges the cached URLs listed in urls-to-purge.txt
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$SRCDIR
Type=simple
ExecStart=${SRCDIR}bin/purge_nginx_cache_file.sh ${PURGEURLLIST} ${origin_server} ${CACHEDIR}

[Install]
WantedBy=multi-user.target

HERE
