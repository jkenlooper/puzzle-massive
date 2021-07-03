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

# Install latest stable version of NGINX
# https://nginx.org/en/linux_packages.html#Ubuntu
# Set up the apt repository for stable nginx packages and pin them.
echo "deb http://nginx.org/packages/ubuntu `lsb_release -cs` nginx" \
      | sudo tee /etc/apt/sources.list.d/nginx.list
echo -e "Package: *\nPin: origin nginx.org\nPin: release o=nginx\nPin-Priority: 900\n" \
      | sudo tee /etc/apt/preferences.d/99nginx
curl -o /tmp/nginx_signing.key https://nginx.org/keys/nginx_signing.key
gpg --list-keys
gpg --dry-run --quiet --import --import-options show-only /tmp/nginx_signing.key | grep --silent 573BFD6B3D8FBC641079A6ABABF5BD827BD9BF62
mv /tmp/nginx_signing.key /etc/apt/trusted.gpg.d/nginx_signing.asc
apt-get --yes update
apt-get --yes install nginx
mkdir -p /etc/nginx/sites-{available,enabled}
rm -f /etc/nginx/conf.d/default.conf
# Verify that the latest stable version of nginx has been installed.
nginx -v 2>&1 | grep --silent '1.20.[0-9]\+' || (echo "Expected stable version nginx 1.20.x" && exit 1)

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

# Install other things needed for the svpng dependency that uses puppeteer
# https://github.com/puppeteer/puppeteer/blob/main/docs/troubleshooting.md
apt-get --yes install ca-certificates fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 lsb-release wget xdg-utils
# Install a fork of svpng that uses node 14
su --command "cd /home/dev && npm install jkenlooper/svpng#28554fa32d57df13ec330e3a4df152172b6080bb" dev
ln -f -s /home/dev/node_modules/svpng/bin/svpng.js /usr/local/bin/svpng

apt-get --yes install redis-server
redis-cli config set maxmemory "500mb"
redis-cli config rewrite

# Remove the default nginx config
rm -f /etc/nginx/sites-enabled/default

echo "checking for missed dependencies of chrome"
ldd /home/dev/node_modules/puppeteer/.local-chromium/linux-*/chrome-linux/chrome | grep not || echo 'no missed dependencies for chrome'
