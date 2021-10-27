#!/usr/bin/env bash

set -eu -o pipefail

# HOSTAPI is from site.cfg
HOSTAPI=$(./bin/puzzle-massive-site-cfg-echo site.cfg HOSTAPI)

# HOSTAPI can be overridden by .env (not currently doing this)
# shellcheck source=/dev/null
source .env

# PORTAPI is from port-registry.cfg
# shellcheck source=/dev/null
source "${PWD}/port-registry.cfg"

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

    proxy_pass http://${HOSTAPI}:${PORTAPI};
HERE

if test -e .vagrant-overrides; then
cat <<-HERE
    proxy_redirect http://${HOSTAPI}:${PORTAPI}/ http://\$host:38682/;
HERE
else
cat <<-HERE
    proxy_redirect http://${HOSTAPI}:${PORTAPI}/ http://\$host/;
HERE
fi

