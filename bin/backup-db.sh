#!/usr/bin/env bash
set -eu -o pipefail

SQLITE_DATABASE_URI=$(./bin/site-cfg.py site.cfg SQLITE_DATABASE_URI);

echo "Before running the backup script; make sure to stop the apps first.";
read -n 1 -p "Continue? y/n " CONTINUE;

if test "$CONTINUE" == "y"; then

echo "Converting pieces to DB from Redis...";

python api/api/jobs/convertPiecesToDB.py site.cfg || exit 1;

DBDUMPFILE="db-$(date +%F).dump.gz";

echo "";
echo "Creating db dump: $DBDUMPFILE";
echo '.dump' | sqlite3 "$SQLITE_DATABASE_URI" | gzip -c > "$DBDUMPFILE";

echo "";
echo "To reconstruct backup";
echo "zcat $DBDUMPFILE | sqlite3 $SQLITE_DATABASE_URI";

fi
