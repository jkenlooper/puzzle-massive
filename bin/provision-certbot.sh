#!/usr/bin/env bash

set -eu -o pipefail

# https://certbot.eff.org/lets-encrypt/ubuntubionic-nginx

# /srv/puzzle-massive/
SRVDIR=$1

# Add Certbot PPA
apt-get update
apt-get install --yes software-properties-common
add-apt-repository universe
add-apt-repository ppa:certbot/certbot
apt-get update

# Install Certbot
apt-get install --yes certbot python-certbot-nginx

# Get the cert and place it in the /.well-known/ location from webroot.
certbot certonly \
  --webroot --webroot-path "${SRVDIR}root/" \
  --domain puzzle.massive.xyz

# The Certbot packages on your system come with a cron job or systemd timer that
# will renew your certificates automatically before they expire. You will not
# need to run Certbot again, unless you change your configuration.
# The command to renew certbot is installed in one of the following locations:
# - /etc/crontab/
# - /etc/cron.*/*
# - systemctl list-timers
echo "Testing automatic certbot cert renewel"
certbot renew --dry-run

# Signal that the certs should now exist.
# The web/puzzle-massive.conf.sh checks if this file exists in
# order to uncomment the lines in the nginx conf for ssl_certificate fields.
touch .has-certs web/puzzle-massive.conf.sh

echo "The certificates have now been generated.  Run make again in order to update nginx conf and make install to update.  The nginx will also need to reload."
