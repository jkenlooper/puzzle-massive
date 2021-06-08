#!/usr/bin/env bash
set -euo pipefail

function usage {
  cat <<USAGE
Usage: ${0} [-h]

Options:
  -h            Show help

Creates the .htpasswd file used for Puzzle Massive basic authentication when
viewing the admin pages.  Existing files will be renamed with a .bak suffix.
This is a wrapper around the htpasswd command. Directly use the htpasswd
command if needing to do anything different. It defaults to use the current
logged in user name (whoami).
USAGE
  exit 0;
}

while getopts ":h" opt; do
  case ${opt} in
    h )
      usage;
      ;;
    \? )
      usage;
      ;;
  esac;
done;
shift "$((OPTIND-1))";

which htpasswd > /dev/null || (echo "No htpasswd command found. Install apache2-utils to get htpasswd command." && exit 1)

cat <<HERE

The admin page uses basic auth. Note that this site does not default to use
a secure protocol (https) and so anyone on your network _could_ see the password
used here. Not really a big deal, but for production deployments the nginx
config is also set to deny any requests to the admin page if not originating
from the internal IP. Admin page access for production requires using a proxy
or changing the nginx config.

HERE

# Set the initial admin user and password. This file is copied to the
# /srv/puzzle-massive/ when installing with `make install`.
if [ -f .htpasswd ]; then
  mv --backup=numbered .htpasswd .htpasswd.bak
fi
echo "Enter password for new .htpasswd file."
htpasswd -c .htpasswd $(whoami);
