#!/bin/bash

echo "Before running the backup script; make sure to stop the apps first.";
read -n 1 -p "Continue? y/n " CONTINUE;

if test $CONTINUE == "y"; then

echo "Converting pieces to DB from Redis...";

./bin/python src/api/jobs/convertPiecesToDB.py chill.cfg || exit 1;

echo "Creating db dump: db-$(date +%F).dump.gz";
echo '.dump' | sqlite3 db | gzip -c > db-$(date +%F).dump.gz
# to reconstruct backup
# zcat db.dump.gz | sqlite3 db

fi
