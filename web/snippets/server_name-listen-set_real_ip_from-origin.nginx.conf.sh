#!/usr/bin/env bash

set -eu -o pipefail

# HOSTORIGIN and HOSTCACHE are from site.cfg
HOSTORIGIN=$(./bin/puzzle-massive-site-cfg-echo site.cfg HOSTORIGIN)
HOSTCACHE=$(./bin/puzzle-massive-site-cfg-echo site.cfg HOSTCACHE)

# HOSTORIGIN and HOSTCACHE can be overridden by .env
# shellcheck source=/dev/null
source .env

# PORTORIGIN is from port-registry.cfg
# shellcheck source=/dev/null
source "${PWD}/port-registry.cfg"

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

  #server_name localhost;
  #server_name \$hostname;
  server_name ${HOSTORIGIN};
  listen      ${PORTORIGIN};
  set_real_ip_from ${HOSTCACHE};
HERE
