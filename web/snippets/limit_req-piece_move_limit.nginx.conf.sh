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
cat <<HEREPIECEMOVELIMIT
    # (1000/200) * 800 = 4 seconds max delay on requests before dropping them
    # with a 503 error. Each subsequent request is delayed 5ms. This rate limit
    # is server wide, but the token limit is on the IP address.
    limit_req zone=piece_move_limit burst=800;
    limit_req_status 503;

HEREPIECEMOVELIMIT
fi
