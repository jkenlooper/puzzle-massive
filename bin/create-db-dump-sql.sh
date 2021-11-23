#!/usr/bin/env bash
set -eu -o pipefail

ENVIRONMENT=$(./bin/puzzle-massive-site-cfg-echo site.cfg ENVIRONMENT || echo 'production')
PUZZLE_FEATURES=$(./bin/puzzle-massive-site-cfg-echo site.cfg PUZZLE_FEATURES || echo 'all')

# Create a tmpdb from `chill initdb` command and site-data.sql.
# Create a copy of site.cfg as tmpsite.cfg to use the temporary database.
# Also set cache to null since the cache directory may not exist yet.
sed "/^CHILL_DATABASE_URI/ s/.*/CHILL_DATABASE_URI='tmpdb'/ ; /^CACHE_TYPE/ s/filesystem/null/" \
   site.cfg > tmpsite.cfg;

# Remove the tmpdb if it exists still from a previous failed attempt.
rm -f tmpdb;

# Initialize database tables for chill
./bin/chill initdb --config tmpsite.cfg;

# Load the main chill-data.yaml as well as any feature specific
# chill-data-feature-*.yaml files
echo ""
for chilly in chill-*.yaml; do
  echo "Loading ${chilly} into chill db."
  ./bin/chill load --yaml "$chilly" --config tmpsite.cfg;
done;

# Load any chill-*.yaml files in the chill-data folder that are not part of
# the main project source code. These are for site specific content.
echo ""
echo "Loading files in chill-data directory:"
find chill-data -name 'chill-*.yaml' -type f | xargs echo
find chill-data -name 'chill-*.yaml' -type f -exec \
  ./bin/chill load --yaml '{}' --config tmpsite.cfg \;

# Load specific chill-data files when in development environment.
echo ""
if test "${ENVIRONMENT}" = 'development'; then
  echo "Loading chill-data/styleguide.yaml into chill db."
  ./bin/chill load --yaml chill-data/styleguide.yaml --config tmpsite.cfg;
fi
echo ""

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
