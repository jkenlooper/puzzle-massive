#!/usr/bin/env bash

set -eu -o pipefail

CLIENT_MAX_BODY_SIZE__PUZZLE_UPLOAD="10m"

# CLIENT_MAX_BODY_SIZE__PUZZLE_UPLOAD can be set in .env
# shellcheck source=/dev/null
source .env

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

    # Prevent POST upload sizes that are larger than this (creates 413 response).
    client_max_body_size ${CLIENT_MAX_BODY_SIZE__PUZZLE_UPLOAD};
HERE
