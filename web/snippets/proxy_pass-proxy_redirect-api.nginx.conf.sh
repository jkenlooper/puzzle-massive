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

# Defaults in case not defined in .env
VAGRANT_FORWARDED_PORT_80=80

if test -e .vagrant-overrides; then
  # override the VAGRANT_FORWARDED_PORT_80 variable
  # shellcheck source=/dev/null
  source .vagrant-overrides
fi

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

    proxy_pass http://${HOSTAPI}:${PORTAPI};
HERE

if test -e .vagrant-overrides; then
cat <<-HERE
    proxy_redirect http://${HOSTAPI}:${PORTAPI}/ http://\$host:$VAGRANT_FORWARDED_PORT_80/;
HERE
else
cat <<-HERE
    proxy_redirect http://${HOSTAPI}:${PORTAPI}/ http://\$host/;
HERE
fi

