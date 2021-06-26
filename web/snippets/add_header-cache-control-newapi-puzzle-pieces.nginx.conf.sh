#!/usr/bin/env bash

set -eu -o pipefail

# shellcheck source=/dev/null
source .env

PUZZLE_PIECES_CACHE_TTL=$(./bin/puzzle-massive-site-cfg-echo site.cfg PUZZLE_PIECES_CACHE_TTL || echo 0)

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

    add_header Cache-Control "public, max-age=${PUZZLE_PIECES_CACHE_TTL}";
HERE
