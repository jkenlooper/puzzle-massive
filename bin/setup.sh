#!/usr/bin/env bash
set -eu -o pipefail

set -x

# https://linuxhint.com/debian_frontend_noninteractive/
export DEBIAN_FRONTEND=noninteractive

apt-get --yes update
apt-get --yes upgrade

# TODO: add these to apt-get commands that show anything about existing
# configuration files that need to be overwritten
# -o Dpkg::Options::="--force-confdef" \
# -o Dpkg::Options::="--force-confold" \

apt-get --yes install ssh rsync

apt-get --yes install \
  gnupg2 \
  ca-certificates \
  lsb-release \
  software-properties-common \
  rsync \
  cron \
  make \
  gcc \
  unzip \
  curl

# Adds the `convert` command which is used to convert source-media/ images to
# the media/ directory.
apt-get --yes install imagemagick

apt-get --yes install \
  python3 \
  python3-dev \
  python3-venv \
  python3-numpy \
  python3-pip \
  python-is-python3 \
  sqlite3

apt-get --yes install \
  awstats

apt-get --yes install libssl-dev
#apt-get --yes install python-pycurl
#apt-get --yes install libcurl4-openssl-dev

# Install support for Pillow
apt-get --yes install python3-pil
# TODO: Are these libs still needed if installing python3-pil?
#apt-get --yes install libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.5-dev tk8.5-dev python3-tk

apt-get --yes install libsqlite3-dev

# Dependencies for piecemaker
apt-get --yes install optipng
apt-get --yes install potrace libffi-dev libxml2-dev python3-lxml python3-xcffib librsvg2-bin

# Dependencies for enforcer (Rtree)
apt-get --yes install libspatialindex6

apt-get --yes install redis-server
redis-cli config set maxmemory "500mb"
redis-cli config rewrite

# Remove the default nginx config
rm -f /etc/nginx/sites-enabled/default
