#!/usr/bin/env bash

set -eu -o pipefail

# https://certbot.eff.org/lets-encrypt/ubuntuxenial-nginx.html

# /srv/puzzle-massive/
SRVDIR=$1

add-apt-repository ppa:certbot/certbot
apt-get update
apt-get install --yes python-certbot-nginx


# Get the cert and place it in the /.well-known/ location from webroot.
certbot certonly \
  --webroot --webroot-path "${SRVDIR}root/" \
  --domain puzzle.massive.xyz

# Add the crontab only if not already there.
if (test ! -f /etc/cron.d/certbot-crontab); then
  cp certbot/certbot-crontab /etc/cron.d/
  chmod 0644 /etc/cron.d/certbot-crontab
fi

# Signal that the certs should now exist.
# The web/puzzle-massive.conf.sh checks if this file exists in
# order to uncomment the lines in the nginx conf for ssl_certificate fields.
touch .has-certs web/puzzle-massive.conf.sh

echo "The certificates have now been generated.  Run make again in order to update nginx conf and make install to update.  The nginx will also need to reload."
