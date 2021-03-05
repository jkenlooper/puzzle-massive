#!/usr/bin/env bash

set -eu -o pipefail

# Get the DOMAIN_NAME
source .env

# Remove any previous copied certs that may exist before provisioning for the
# first time. This prevents downtime if the certs were simply copied over from
# a different server.
if [ ! -n "$(command -v certbot)" ]; then
  echo "certbot hasn't been provisioned before; checking if existing certs need to be removed in order for certbot to be configured correctly."
  if [ -e /etc/letsencrypt/live/puzzle.massive.xyz ]; then
    rm -rf --verbose /etc/letsencrypt/live/puzzle.massive.xyz
  fi
fi

# https://certbot.eff.org/lets-encrypt/ubuntufocal-nginx

# Ensure that your version of snapd is up to date
snap install core
snap refresh core

# Remove any previous install if applicable
apt-get remove certbot

# Install Certbot
snap install --classic certbot

# Prepare the Certbot command
if [ ! -e /usr/bin/certbot ]; then
  ln -s /snap/bin/certbot /usr/bin/certbot
fi

# /srv/puzzle-massive/
SRVDIR=$1

# Get the cert and place it in the /.well-known/ location from webroot.
certbot certonly \
  --webroot --webroot-path "${SRVDIR}root/" \
  --domain ${DOMAIN_NAME}

# The Certbot packages on your system come with a cron job or systemd timer that
# will renew your certificates automatically before they expire. You will not
# need to run Certbot again, unless you change your configuration.
# The command to renew certbot is installed in one of the following locations:
# - /etc/crontab/
# - /etc/cron.*/*
# - systemctl list-timers
echo "Testing automatic certbot cert renewal"
certbot renew --dry-run

# Signal that the certs should now exist.
# The web/puzzle-massive.conf.sh checks if this file exists in
# order to uncomment the lines in the nginx conf for ssl_certificate fields.
touch .has-certs web/puzzle-massive.conf.sh

echo "The certificates have now been generated.  Run make again in order to update nginx conf and make install to update.  The nginx will also need to reload."
