#!/usr/bin/env bash
set -eu -o pipefail

function usage {
  cat <<USAGE
Usage: ${0} [-h] <dist_file.tar.gz>

Options:
  -h            Show help

Quickly deploys a dist file on a server that has already been setup. This
follows the In-Place Deployment guide and takes a dist file
(puzzle-massive-2.x.x.tar.gz) as the first argument.
A backup is made and placed in the /home/dev/ directory in case a rollback needs
to happen.

Should be run with sudo.
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

DIST_FILE=$1

if [ ! -e $DIST_FILE ]; then
  echo "The '${DIST_FILE}' should be a dist file."
  exit 1
fi

if [ $(whoami) != root ]; then
  echo "This script should be run as root or use sudo"
  exit 2
fi

set -x

cd /usr/local/src/puzzle-massive/;

su dev -c "printf 'Updating...' > /srv/puzzle-massive/root/puzzle-massive-message.html";
./bin/appctl.sh stop;
#systemctl start puzzle-massive-api;
./bin/clear_nginx_cache.sh -y;
#sleep 5
#su dev -c "./bin/backup.sh -c";
#sleep 5
#systemctl stop puzzle-massive-api;
#systemctl reload nginx;

cd /home/dev/;
if [ -d puzzle-massive-$(date +%F) ]; then
  TMPDIR=$(mktemp --directory)
  if [ -e puzzle-massive-$(date +%F).tar ]; then
    mv --backup=numbered puzzle-massive-$(date +%F).tar puzzle-massive-$(date +%F).bak.tar
  fi
  mv puzzle-massive-$(date +%F) $TMPDIR
  tar --create --file puzzle-massive-$(date +%F).tar --directory=$TMPDIR puzzle-massive-$(date +%F)
fi
mv --backup=existing /usr/local/src/puzzle-massive puzzle-massive-$(date +%F);
tar --directory=/usr/local/src/ --extract --gunzip -f $DIST_FILE
chown -R dev:dev /usr/local/src/puzzle-massive
su dev -c "cp puzzle-massive-$(date +%F)/.env /usr/local/src/puzzle-massive/";

# Add .has-certs file if site has already been setup with bin/provision-certbot.sh
su dev -c "cp puzzle-massive-$(date +%F)/.has-certs /usr/local/src/puzzle-massive/" || echo "No certs?";

su dev -c "python -m venv .";

su dev -c "make ENVIRONMENT=production";

su dev -c "./bin/python api/api/jobs/migrate_puzzle_massive_database_version.py";

# Update any bit icon authors and add new bit icons if applicable
su dev -c "./bin/python api/api/jobs/insert-or-replace-bit-icons.py";

# Update the enabled puzzle features if applicable
su dev -c "./bin/python api/api/update_enabled_puzzle_features.py";

make ENVIRONMENT=production install;
nginx -t;
systemctl reload nginx;
su dev -c "printf '' > /srv/puzzle-massive/root/puzzle-massive-message.html";
./bin/clear_nginx_cache.sh -y;

./bin/appctl.sh status;
