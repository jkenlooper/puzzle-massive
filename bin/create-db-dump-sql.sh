#!/usr/bin/env bash
set -eu -o pipefail

# Create a tmpdb from chill-data.sql and tmpsite.cfg to use the temporary
# database.
sed "/^CHILL_DATABASE_URI/ s/sqlite:\/\/\/.*db/sqlite:\/\/\/tmpdb/" site.cfg > tmpsite.cfg
sqlite3 tmpdb < chill-data.sql

for chilly in chill-*.yaml; do
  chill load --yaml "$chilly" --config tmpsite.cfg;
done;

echo 'DROP TABLE if exists Chill;' > db.dump.sql
echo 'DROP TABLE if exists Node;' >> db.dump.sql
echo 'DROP TABLE if exists Node_Node;' >> db.dump.sql
echo 'DROP TABLE if exists Query;' >> db.dump.sql
echo 'DROP TABLE if exists Route;' >> db.dump.sql
echo 'DROP TABLE if exists Template;' >> db.dump.sql

echo '.dump' | sqlite3 tmpdb >> db.dump.sql;

# Remove no longer needed temporary files.
rm -f tmpdb tmpsite.cfg;

