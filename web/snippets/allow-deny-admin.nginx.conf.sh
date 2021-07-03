#!/usr/bin/env bash

set -eu -o pipefail

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

    # Conditionally sets the allow and deny for admin routes.
    # This is usually for supporting vagrant setup.
HERE

if test ! -e .vagrant-overrides; then
cat <<-HERE

    # Requires using SOCKS proxy (ssh -D 8080 user@host)
    allow 127.0.0.1;
    deny all;
HERE
fi
