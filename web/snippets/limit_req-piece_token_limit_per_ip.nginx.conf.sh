#!/usr/bin/env bash

set -eu -o pipefail

# shellcheck source=/dev/null
source .env

DATE=$(date)

# Defaults in case not defined in .env
PUZZLE_RULES='all'

PUZZLE_RULES=$(./bin/puzzle-massive-site-cfg-echo site.cfg PUZZLE_RULES || echo ${PUZZLE_RULES})

USE_PIECE_PUBLISH_LIMIT=0
if [[ "$PUZZLE_RULES" =~ (^|[^[:alnum:]_])(all|nginx_piece_publish_limit)([^[:alnum:]_]|$) ]]; then
  USE_PIECE_PUBLISH_LIMIT=1;
fi

cat <<-HERE
    # File generated from $0
    # on ${DATE}
HERE

if test $USE_PIECE_PUBLISH_LIMIT -eq 1; then
cat <<HEREPIECETOKENLIMIT
    # Limit rate for an IP to prevent hitting 503 errors. Burst is set at 120
    # with the 60 requests a second rate. (1000/60) * 120 = 2 seconds. Which will
    # give at most a 2 second delay before dropping requests with 429 error.
    limit_req zone=piece_token_limit_per_ip burst=120;
    limit_req_status 429;
HEREPIECETOKENLIMIT
fi
