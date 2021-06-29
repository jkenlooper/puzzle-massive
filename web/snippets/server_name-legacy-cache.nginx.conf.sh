#!/usr/bin/env bash

set -eu -o pipefail

ENVIRONMENT=$1

# DOMAIN_NAME is from .env
# shellcheck source=/dev/null
source .env

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

HERE

if test "${ENVIRONMENT}" == 'development'; then
INTERNALIP=$(hostname -I | cut -d' ' -f1)
cat <<HEREBEDEVELOPMENT
  # Only when in development should the site be accessible via internal ip.
  # This makes it easier to test with other devices that may not be able to
  # update a /etc/hosts file.
  # Use localhost when developing in a vm with Vagrant (see forwarded_port in
  # VagrantFile).
  # external-puzzle-massive server_name is used for internal requests that need
  # to benefit from nginx cache.
  server_name local-puzzle-massive external-puzzle-massive localhost $INTERNALIP \$hostname;
HEREBEDEVELOPMENT
else
cat <<HEREBEPRODUCTION
  # external-puzzle-massive server_name is used for internal requests that need
  # to benefit from nginx cache.
  server_name external-puzzle-massive puzzle-massive-blue puzzle-massive-green ${DOMAIN_NAME} \$hostname;
HEREBEPRODUCTION
fi
