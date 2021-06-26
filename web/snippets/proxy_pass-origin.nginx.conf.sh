#!/usr/bin/env bash

set -eu -o pipefail

# HOSTORIGIN is from site.cfg
HOSTORIGIN=$(./bin/puzzle-massive-site-cfg-echo site.cfg HOSTORIGIN)

# HOSTORIGIN can be overridden by .env (not currently doing this)
# shellcheck source=/dev/null
source .env

# PORTORIGIN is from port-registry.cfg
# shellcheck source=/dev/null
source "${PWD}/port-registry.cfg"

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

    proxy_pass http://${HOSTORIGIN}:${PORTORIGIN};
HERE
