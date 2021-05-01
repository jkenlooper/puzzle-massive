#!/usr/bin/env bash
set -eu -o pipefail

apt-get --yes update
apt-get --yes upgrade

apt-get --yes install \
  software-properties-common \
  rsync \
  nginx \
  apache2-utils \
  cron \
  make \
  gcc \
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
apt-get --yes install libspatialindex6
apt-get --yes install optipng
curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
apt-get install -y nodejs

apt-get --yes install potrace libffi-dev libxml2-dev python3-lxml python3-xcffib
npm install -g svgo
npm install -g --unsafe-perm=true svpng


apt-get --yes install redis-server
redis-cli config set maxmemory "500mb"
redis-cli config rewrite

# Remove the default nginx config
rm -f /etc/nginx/sites-enabled/default
