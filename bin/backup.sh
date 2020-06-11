#!/usr/bin/env bash
set -eu -o pipefail

function usage {
  cat <<USAGE
Usage: ${0} [-h] [-d <backup-directory-path>] [-c] [<backup-filename>]

Options:
  -h            Show help
  -d directory  Set the directory to store backup files in [default: ./]
  -w            Name backup file with the day of week
  -c            Cleanup redis data after transferring to DB

Creates a backup file of the database.  It first converts the redis piece data
to the database and runs any necessary scheduler tasks for batched redis data.
Uses today's date when creating the backup file if not specified.
USAGE
  exit 0;
}

WEEKDAY_BACKUP=;
CLEANUP=;
BACKUP_DIRECTORY=$(pwd)
while getopts ":hd:wc" opt; do
  case ${opt} in
    h )
      usage;
      ;;
    d )
      BACKUP_DIRECTORY=${OPTARG};
      ;;
    w )
      WEEKDAY_BACKUP=1;
      ;;
    c )
      CLEANUP="--cleanup";
      ;;
    \? )
      usage;
      ;;
  esac;
done;
shift "$((OPTIND-1))";

SQLITE_DATABASE_URI=$(./bin/python bin/site-cfg.py site.cfg SQLITE_DATABASE_URI);

DBOWNER=$(stat -c '%U' "${SQLITE_DATABASE_URI}")
if test "${USER}" \!= "${DBOWNER}"; then
  echo "This should be run with the same user that owns the db file at ${SQLITE_DATABASE_URI}."
  echo "For example: sudo su ${DBOWNER}"
  exit 1;
fi

echo "Converting pieces to DB from Redis...";

./bin/python api/api/jobs/convertPiecesToDB.py ${CLEANUP} || exit 1;

echo "Running one-off scheduler tasks to clean up any batched data";
./bin/puzzle-massive-scheduler --task UpdatePlayer || exit 1;
./bin/puzzle-massive-scheduler --task UpdatePuzzleStats || exit 1;
./bin/puzzle-massive-scheduler --task UpdateModifiedDateOnPuzzle || exit 1;

# Allow passing in a file path of where to save the db dump file
if [ -n "${1-}" ]; then
DBDUMPFILE="$1";
else
    if [ -n "${WEEKDAY_BACKUP-}" ]; then
        DBDUMPFILE="db-$(date --utc '+%a').dump.gz";
    else
        DBDUMPFILE="db-$(date --iso-8601 --utc).dump.gz";
    fi;
fi;

echo "";
echo "Creating db dump: ${BACKUP_DIRECTORY}/${DBDUMPFILE}";
echo '.dump' | sqlite3 "$SQLITE_DATABASE_URI" | gzip -c > "${BACKUP_DIRECTORY}/${DBDUMPFILE}";

echo "";
echo "To reconstruct backup";
echo "zcat ${BACKUP_DIRECTORY}/${DBDUMPFILE} | sqlite3 $SQLITE_DATABASE_URI";
