#!/usr/bin/env bash
set -eu -o pipefail

NGINXCACHEDIR=/var/lib/puzzle-massive/cache/

# Clear the cache
if test -d ${NGINXCACHEDIR}; then
    read -n1 -p "Remove all cache files in ${NGINXCACHEDIR} ? [y/n]" CONFIRM;
    if test "${CONFIRM}" == 'y'; then
        rm -rf ${NGINXCACHEDIR:?}/*;
    fi
fi

