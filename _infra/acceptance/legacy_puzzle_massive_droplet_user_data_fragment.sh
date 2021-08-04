## Embedded into the generated user_data script

cd /home/dev/

# AWS S3 CLI has been configured via the user_data from droplet-setup.sh

# Get the dist
tar --directory=/usr/local/src/ --extract --gunzip -f $ARTIFACT
cd /usr/local/src/puzzle-massive;

mv $ENV_FILE .env

chown dev:dev /usr/local/src/puzzle-massive;

# TODO: Install new server certs for this domain.
# TODO: Add provisioning command to remove/unregister server certs when this is
# destroyed.

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

# TODO: continue with a recent copy of production data
exit 0

./bin/appctl.sh stop -f;

su --command '
  rm /var/lib/puzzle-massive/sqlite3/db*;
  rm -rf /var/lib/puzzle-massive/archive/*
  rm -rf /srv/puzzle-massive/resources/*;
' dev
./bin/clear_nginx_cache.sh;

# Use `flushdb` on the new server to remove all keys on the redis database.
su --command '
  REDIS_DB=$(./bin/puzzle-massive-site-cfg-echo site.cfg REDIS_DB);
  redis-cli -n ${REDIS_DB} flushdb
' dev

# TODO: get a copy of the last backup of production data from S3
#aws s3 cp --endpoint=https://$backup_BUCKET_REGION.digitaloceanspaces.com s3://$backup_BUCKET/production_data ./


