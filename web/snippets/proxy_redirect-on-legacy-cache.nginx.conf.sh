#!/usr/bin/env bash

set -eu -o pipefail

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

    # Conditionally sets the proxy_redirect if host is not serving on port 80.
    # This is usually for supporting vagrant setup.
HERE

if test -e .vagrant-overrides; then
cat <<-HERE
    proxy_redirect http://\$host/ http://\$host:$VAGRANT_FORWARDED_PORT_80/;
HERE
fi
