#!/usr/bin/env bash

set -eu -o pipefail

ENVIRONMENT=$1

# shellcheck source=/dev/null
source .env

SRVDIR=/srv/puzzle-massive/
DATE=$(date)

if test "${ENVIRONMENT}" != 'development'; then
  root_dir=${SRVDIR}
else
  root_dir=${PWD}
fi

cat <<-HERE
# File generated from $0
# on ${DATE}

location /dist/ {
  expires \$cache_expire;
  add_header Cache-Control "public";
  root ${root_dir};
  try_files \$uri =404;
}
HERE
