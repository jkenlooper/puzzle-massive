#!/usr/bin/env bash
set -eu -o pipefail

set -x

export DEBIAN_FRONTEND=noninteractive

apt-get --yes update
apt-get --yes install curl gnupg2 ca-certificates lsb-release

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
nginx -v 2>&1 | grep --silent '1.24.[0-9]\+' || (echo "Expected stable version nginx 1.24.x" && exit 1)
