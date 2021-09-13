## Embedded into the generated user_data script

cd /home/dev/

# AWS S3 CLI has been configured via the user_data from droplet-setup.sh

# Get the dist
tar --directory=/usr/local/src/ --extract --gunzip -f $ARTIFACT
cd /usr/local/src/puzzle-massive;

mv $ENV_FILE .env

chown dev:dev /usr/local/src/puzzle-massive;

su --command '
  python -m venv .;
  make ENVIRONMENT=production;
' dev

make ENVIRONMENT=production install;
./bin/appctl.sh stop -f;

su --command '
  ./bin/python api/api/create_database.py site.cfg;
  ./bin/python api/api/jobs/insert-or-replace-bit-icons.py
  ./bin/python api/api/update_enabled_puzzle_features.py;
' dev

# Prove that the app starts without production data
./bin/appctl.sh start;

# is-active will fail with error code if any service had errors
./bin/appctl.sh is-active;

# Continue only if database dump file is not empty.
DBDUMPFILE=/home/dev/db.dump.gz
test -s $DBDUMPFILE || (echo "The $DBDUMPFILE is empty. Done setting up." && exit 0)
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
  ./bin/python api/api/update_enabled_puzzle_features.py;
' dev

./bin/appctl.sh start;
./bin/appctl.sh is-active;
