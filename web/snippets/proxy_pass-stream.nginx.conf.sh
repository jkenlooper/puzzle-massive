#!/usr/bin/env bash

set -eu -o pipefail

# HOSTSTREAM is from site.cfg
HOSTSTREAM=$(./bin/puzzle-massive-site-cfg-echo site.cfg HOSTSTREAM)

# HOSTSTREAM can be overridden by .env (not currently doing this)
# shellcheck source=/dev/null
source .env

# PORTSTREAM is from port-registry.cfg
# shellcheck source=/dev/null
source "${PWD}/port-registry.cfg"

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

    proxy_pass http://${HOSTSTREAM}:${PORTSTREAM};
HERE
