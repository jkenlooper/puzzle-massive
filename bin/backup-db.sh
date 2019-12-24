#!/usr/bin/env bash
set -eu -o pipefail

SQLITE_DATABASE_URI=$(./bin/site-cfg.py site.cfg SQLITE_DATABASE_URI);

echo "Before running the backup script; make sure to stop the apps first.";
read -n 1 -p "Continue? y/n " CONTINUE;

if test "$CONTINUE" == "y"; then

echo "Converting pieces to DB from Redis...";

python api/api/jobs/convertPiecesToDB.py site.cfg || exit 1;

echo "Running one-off scheduler tasks to clean up any batched data";
python api/api/scheduler.py site.cfg UpdatePlayer || exit 1;
python api/api/scheduler.py site.cfg UpdatePuzzleStats || exit 1;
#TODO: check other scheduler tasks to see if any others need to be ran.

# Allow passing in a file path of where to save the db dump file
if [ -n "${1-}" ]; then
DBDUMPFILE="$1";
else
DBDUMPFILE="db-$(date --iso-8601 --utc).dump.gz";
fi;

echo "";
echo "Creating db dump: $DBDUMPFILE";
echo '.dump' | sqlite3 "$SQLITE_DATABASE_URI" | gzip -c > "$DBDUMPFILE";

echo "";
echo "To reconstruct backup";
echo "zcat $DBDUMPFILE | sqlite3 $SQLITE_DATABASE_URI";

fi
