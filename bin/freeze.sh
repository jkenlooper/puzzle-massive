#!/usr/bin/env bash
set -eu -o pipefail

FROZEN_TAR=$1

# Create a tmp db from db.dump.sql and tmp site.cfg to use the temporary
# database.
sed "/^CHILL_DATABASE_URI/ s/.*/CHILL_DATABASE_URI='tmpdb'/" site.cfg > tmpsite.cfg;
sqlite3 tmpdb < db.dump.sql

bin/chill freeze --config tmpsite.cfg

# Remove no longer needed temporary files.
rm -f tmpdb tmpsite.cfg;

tar --create --auto-compress --file "${FROZEN_TAR}" frozen/

# Remove frozen files that were generated since the tar should be used to
# install.
rm -rf frozen
