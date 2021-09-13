## Embedded into the generated user_data script

cd /home/dev/

# Get the source code
git clone $ARTIFACT puzzle-massive
cd puzzle-massive

cp $ENV_FILE .env
chown -R dev:dev ../puzzle-massive

# Standard build stuff
su --command '
npm install;
npm run debug;
' dev

mkdir -p /usr/local/src/puzzle-massive;
chown dev:dev /usr/local/src/puzzle-massive;

# Sends files to the /usr/local/src/puzzle-massive directory
./bin/devsync.sh . /usr/local/src/puzzle-massive/
chown -R dev:dev /usr/local/src/puzzle-massive;

cd /usr/local/src/puzzle-massive;
su --command '
  python -m venv .;
  make;
' dev
make install;
./bin/appctl.sh stop -f;
su --command '
  ./bin/python api/api/create_database.py site.cfg;
  ./bin/python api/api/jobs/insert-or-replace-bit-icons.py;
  ./bin/python api/api/update_enabled_puzzle_features.py;
' dev
./bin/appctl.sh start;
./bin/appctl.sh status;

# is-active will fail with error code if any service had errors
./bin/appctl.sh is-active;

# Continue only if database dump file is not empty.
DBDUMPFILE=/home/dev/db.dump.gz
echo "Checking if the $DBDUMPFILE is empty. Will stop here if it is."
test -s $DBDUMPFILE || exit 0
# The rest of this should usually just be applicable for the Acceptance or Development environments.

./bin/appctl.sh stop -f;

su --command '
  rm /var/lib/puzzle-massive/sqlite3/db*;
  rm -rf /var/lib/puzzle-massive/archive/*
  rm -rf /srv/puzzle-massive/resources/*;
' dev
./bin/clear_nginx_cache.sh -y;

# Use `flushdb` on the new server to remove all keys on the redis database.
su --command '
  REDIS_DB=$(./bin/puzzle-massive-site-cfg-echo site.cfg REDIS_DB);
  redis-cli -n ${REDIS_DB} flushdb
' dev

# The rsync of puzzle resources should be done later with an Ansible playbook.

su --command '
  touch /var/lib/puzzle-massive/sqlite3/db
  zcat $DBDUMPFILE | sqlite3 /var/lib/puzzle-massive/sqlite3/db
  cat db.dump.sql | sqlite3 /var/lib/puzzle-massive/sqlite3/db
  echo "pragma journal_mode=wal" | sqlite3 /var/lib/puzzle-massive/sqlite3/db

  # TODO: run migrate scripts here?

  ./bin/python api/api/jobs/insert-or-replace-bit-icons.py
  ./bin/python api/api/update_enabled_puzzle_features.py
' dev

./bin/appctl.sh start;
./bin/appctl.sh is-active;
