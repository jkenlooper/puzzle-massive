#!/usr/bin/env bash
set -e -o pipefail

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

EPHEMERAL_ARCHIVE_ENDPOINT_URL=
EPHEMERAL_ARCHIVE_BUCKET=
source .env

WEEKDAY_BACKUP=;
TIMESTAMP_BACKUP=;
CLEANUP=;
BACKUP_DIRECTORY=$(pwd)
while getopts ":hd:wtc" opt; do
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
    t )
      TIMESTAMP_BACKUP=1;
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

SQLITE_DATABASE_URI=$(./bin/puzzle-massive-site-cfg-echo site.cfg SQLITE_DATABASE_URI);

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
  elif [ -n "${TIMESTAMP_BACKUP-}" ]; then
    DBDUMPFILE="db-$(date --utc '+%F-%H%M%S').dump.gz";
  else
    DBDUMPFILE="db-$(date --iso-8601 --utc).dump.gz";
    if [ -e "${BACKUP_DIRECTORY}/${DBDUMPFILE}" ]; then
      DBDUMPFILE_bak="db-$(date --iso-8601 --utc).bak.dump.gz";
      mv --backup=numbered "${BACKUP_DIRECTORY}/${DBDUMPFILE}" "${BACKUP_DIRECTORY}/${DBDUMPFILE_bak}"
    fi
  fi;
fi;

echo "";
echo "Creating db dump: ${BACKUP_DIRECTORY}/${DBDUMPFILE}";
echo '.dump' | sqlite3 "$SQLITE_DATABASE_URI" | gzip -c > "${BACKUP_DIRECTORY}/${DBDUMPFILE}";

echo "";
echo "To reconstruct backup";
echo "zcat ${BACKUP_DIRECTORY}/${DBDUMPFILE} | sqlite3 $SQLITE_DATABASE_URI";

if [ -n "${EPHEMERAL_ARCHIVE_ENDPOINT_URL}" -a -n "${EPHEMERAL_ARCHIVE_BUCKET}" ]; then
    echo "";
    echo "Uploading ${DBDUMPFILE} to S3 bucket ${EPHEMERAL_ARCHIVE_BUCKET}";
    echo "zcat ${BACKUP_DIRECTORY}/${DBDUMPFILE} | sqlite3 $SQLITE_DATABASE_URI";
    aws s3 cp --endpoint=${EPHEMERAL_ARCHIVE_ENDPOINT_URL} "${BACKUP_DIRECTORY}/${DBDUMPFILE}" s3://${EPHEMERAL_ARCHIVE_BUCKET}/${DBDUMPFILE}
    # Sleep after the s3 upload just in case it didn't fully finish. This is
    # probably not needed, but it doesn't hurt anything here.
    sleep 1
    echo "Uploaded date stamped db backup to ${EPHEMERAL_ARCHIVE_BUCKET} s3 bucket."
    echo "Renaming the ${DBDUMPFILE} to a weekday filename to preserve disk space."
    weekday_backup_db_dump_file="${EPHEMERAL_ARCHIVE_BUCKET}__db-$(date --utc '+%a').dump.gz";
    mv --verbose "${BACKUP_DIRECTORY}/${DBDUMPFILE}" "${BACKUP_DIRECTORY}/${weekday_backup_db_dump_file}"
fi
