#!/usr/bin/env bash

set -eu -o pipefail

# HOME_PAGE_ROUTE is from .env
# shellcheck source=/dev/null
source .env

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

  # Home page goes to the chill/site/front/ (the default) and strip query params
  rewrite ^/$ ${HOME_PAGE_ROUTE}? last;
HERE
