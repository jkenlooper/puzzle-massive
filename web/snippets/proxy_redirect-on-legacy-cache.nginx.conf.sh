#!/usr/bin/env bash

set -eu -o pipefail

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

    # Conditionally sets the proxy_redirect if host is not serving on port 80.
    # This is usually for supporting vagrant setup.
HERE

if test -e .vagrant-overrides; then
cat <<-HERE
    proxy_redirect http://\$host/ http://\$host:38682/;
HERE
fi
