#!/usr/bin/env bash

set -eu -o pipefail

ENVIRONMENT=$1

# Get the DOMAIN_NAME
source .env

DATE=$(date)

cat <<-HERE
    # File generated from $0
    # on ${DATE}

HERE

if test -e .has-certs; then

  if test -e "/etc/nginx/ssl/localhost.crt"; then

cat <<-HEREENABLESSLCERTS
  # TLS certs created for development
  ssl_certificate /etc/nginx/ssl/localhost.crt;
  ssl_certificate_key /etc/nginx/ssl/localhost.key;
HEREENABLESSLCERTS

  elif test -e "/etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem"; then

    #test which certbot || (echo "# Certbot not installed" && exit 1)
    # This script is not run with sudo...the `certbot certificate` command needs sudo.
    # If a certificate is being copied over from a different server; certbot
    # might not be provisioned on this server.
    # So the certbot command is not required in order to run this script.

cat <<-HEREENABLESSLCERTS
  # TLS certs created from certbot letsencrypt
  ssl_certificate /etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/${DOMAIN_NAME}/privkey.pem;
HEREENABLESSLCERTS

  else

cat <<-HERENOCERTS
  # No certs found at either location!
  # Production:
  #   /etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem
  # Development:
  #   /etc/nginx/ssl/localhost.crt
HERENOCERTS

    exit 1

  fi

cat <<-HEREBECERTS
  listen 443 ssl http2;
HEREBECERTS

fi
