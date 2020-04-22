#!/usr/bin/env bash
set -eu -o pipefail

# Create a tmpdb from `chill initdb` command and site-data.sql.
# Create a copy of site.cfg as tmpsite.cfg to use the temporary database.
# Also set cache to null since the cache directory may not exist yet.
sed "/^CHILL_DATABASE_URI/ s/sqlite:\/\/\/.*db/sqlite:\/\/\/tmpdb/ ; /^CACHE_TYPE/ s/filesystem/null/" \
   site.cfg > tmpsite.cfg;

# Remove the tmpdb if it exists still from a previous failed attempt.
rm -f tmpdb;

# Initialize database tables for chill
chill initdb --config tmpsite.cfg;

for chilly in chill-*.yaml; do
  chill load --yaml "$chilly" --config tmpsite.cfg;
done;

rm -f db.dump.sql;
{
  echo 'DROP TABLE if exists Chill;';
  echo 'DROP TABLE if exists Node;';
  echo 'DROP TABLE if exists Node_Node;';
  echo 'DROP TABLE if exists Query;';
  echo 'DROP TABLE if exists Route;';
  echo 'DROP TABLE if exists Template;';
  echo '.dump' | sqlite3 tmpdb;
  cat site-data.sql;
} >> db.dump.sql;

# Remove no longer needed temporary files.
rm -f tmpdb tmpsite.cfg;

