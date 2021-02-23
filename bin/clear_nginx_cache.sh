#!/usr/bin/env bash
set -eu -o pipefail

NGINXCACHEDIR=/var/lib/puzzle-massive/cache/
CONFIRM=n

function usage {
  cat <<USAGE
Usage: ${0} [-h] [-y]

Options:
  -h            Show help
  -y            Skip confirmation prompt

Removes all cache files in ${NGINXCACHEDIR}
USAGE
  exit 0;
}

while getopts ":hy" opt; do
  case ${opt} in
    h )
      usage;
      ;;
    y )
      CONFIRM='y';
      ;;
    \? )
      usage;
      ;;
  esac;
done;
shift "$((OPTIND-1))";

# Clear the cache
if test -d ${NGINXCACHEDIR}; then
    if test "${CONFIRM}" != 'y'; then
      read -n1 -p "Remove all cache files in ${NGINXCACHEDIR} ? [y/n]" CONFIRM;
    fi
    if test "${CONFIRM}" == 'y'; then
        rm -rf ${NGINXCACHEDIR:?}/*;
    fi
fi

