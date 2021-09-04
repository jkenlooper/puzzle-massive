#!/usr/bin/env bash

set -eu -o pipefail

# HOSTCHILL is from site.cfg
HOSTCHILL=$(./bin/puzzle-massive-site-cfg-echo site.cfg HOSTCHILL)

# HOSTCHILL can be overridden by .env (not currently doing this)
# shellcheck source=/dev/null
source .env

# PORTCHILL is from port-registry.cfg
# shellcheck source=/dev/null
source "${PWD}/port-registry.cfg"

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

    proxy_pass http://${HOSTCHILL}:${PORTCHILL};
    proxy_redirect http://${HOSTCHILL}:${PORTCHILL}/ http://\$host/;
HERE
