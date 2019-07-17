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
  curl

apt-get --yes install \
  python \
  python-dev \
  python3-dev \
  python-pip \
  python-numpy \
  sqlite3 \
  libpq-dev \
  python-psycopg2 \
  virtualenv

apt-get --yes install \
  awstats

apt-get --yes install libssl-dev
#apt-get --yes install python-pycurl
apt-get --yes install imagemagick
#apt-get --yes install libcurl4-openssl-dev

# Install support for Pillow
apt-get --yes install python3-pil
# TODO: Are these libs still needed if installing python3-pil?
apt-get --yes install libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.5-dev tk8.5-dev python-tk

apt-get --yes install libsqlite3-dev

# Dependencies for piecemaker
apt-get --yes install optipng
curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -
apt-get install -y nodejs # also installs npm

apt-get --yes install potrace libffi-dev python-libxml2 libxml2-dev python-lxml python-xcffib
apt-get --yes install libcairo2-dev
apt-get --yes install python-cairo
npm install -g svgo


apt-get --yes install redis-server
redis-cli config set maxmemory "100mb"
redis-cli config rewrite

# Remove the default nginx config
rm /etc/nginx/sites-enabled/default
