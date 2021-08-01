#!/usr/bin/env bash

set -eu -o pipefail

ENVIRONMENT=$1

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

HERE

if test -e .has-certs; then
cat <<-HEREBECERTS
  listen 443 ssl http2;
HEREBECERTS
fi

if test "${ENVIRONMENT}" == 'development'; then

  if test -e .has-certs; then
cat <<-HEREENABLESSLCERTS
  # certs created for local development
  ssl_certificate "/etc/nginx/ssl/local-puzzle-massive.crt";
  ssl_certificate_key "/etc/nginx/ssl/local-puzzle-massive.key";
HEREENABLESSLCERTS
  else
cat <<-HERETODOSSLCERTS
  # certs for local development can be created by running './bin/provision-local-ssl-certs.sh'
  # uncomment after they exist (run make again)
  #ssl_certificate "/etc/nginx/ssl/local-puzzle-massive.crt";
  #ssl_certificate_key "/etc/nginx/ssl/local-puzzle-massive.key";
HERETODOSSLCERTS
  fi

else

  if test -e .has-certs; then
cat <<-HEREENABLESSLCERTS
  # certs created from certbot
  ssl_certificate /etc/letsencrypt/live/puzzle.massive.xyz/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/puzzle.massive.xyz/privkey.pem;
HEREENABLESSLCERTS
  else
cat <<-HERETODOSSLCERTS
  # certs can be created from running 'bin/provision-certbot.sh /srv/puzzle-massive'
  #ssl_certificate /etc/letsencrypt/live/puzzle.massive.xyz/fullchain.pem;
  #ssl_certificate_key /etc/letsencrypt/live/puzzle.massive.xyz/privkey.pem;
HERETODOSSLCERTS
  fi

fi
