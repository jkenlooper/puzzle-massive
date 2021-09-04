#!/usr/bin/env bash

set -eu -o pipefail

# HOSTPUBLISH is from site.cfg
HOSTPUBLISH=$(./bin/puzzle-massive-site-cfg-echo site.cfg HOSTPUBLISH)

# HOSTPUBLISH can be overridden by .env (not currently doing this)
# shellcheck source=/dev/null
source .env

# PORTPUBLISH is from port-registry.cfg
# shellcheck source=/dev/null
source "${PWD}/port-registry.cfg"

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

    proxy_pass http://${HOSTPUBLISH}:${PORTPUBLISH};
    proxy_redirect http://${HOSTPUBLISH}:${PORTPUBLISH}/ http://\$host/;
HERE
