#!/usr/bin/env bash
set -eu -o pipefail

# /srv/puzzle-massive/
SRVDIR=$1

# /etc/nginx/
NGINXDIR=$2

# /var/log/nginx/puzzle-massive/
NGINXLOGDIR=$3

# /var/log/awstats/puzzle-massive/
AWSTATSLOGDIR=$4

# /etc/systemd/system/
SYSTEMDDIR=$5

# All processes using a database must be on the same host computer; WAL does not
# work over a network filesystem. If using Vagrant, the db file can't be in
# a shared directory.
# /var/lib/puzzle-massive/sqlite3/
DATABASEDIR=$6

# /var/lib/puzzle-massive/archive/
ARCHIVEDIR=$7

# /var/lib/puzzle-massive/cache/
CACHEDIR=$8

mkdir -p "${SRVDIR}root/";
chown -R dev:dev "${SRVDIR}root/";
rsync --archive \
  --inplace \
  --delete \
  --exclude=.well-known \
  --itemize-changes \
  root/ "${SRVDIR}root/";
echo "rsynced files in root/ to ${SRVDIR}root/";

mkdir -p "${SRVDIR}resources/";
chown -R dev:dev "${SRVDIR}resources/";

if (test ! -d "${SRVDIR}media/bit-icons/"); then
  echo "Adding the initial set of bit-icons to ${SRVDIR}media/bit-icons/";
  mkdir -p "${SRVDIR}media/bit-icons/";
  chown -R dev:dev "${SRVDIR}media/bit-icons/";
  tar --directory="${SRVDIR}media/bit-icons/" -xz -f resources/bit-icons.tar.gz;
fi

# TODO: not using static files yet
#FROZENTMP=$(mktemp -d);
#tar --directory="${FROZENTMP}" --gunzip --extract -f frozen.tar.gz
#rsync --archive \
#  --delete \
#  --itemize-changes \
#  "${FROZENTMP}/frozen/" "${SRVDIR}frozen/";
#echo "rsynced files in frozen.tar.gz to ${SRVDIR}frozen/";
#rm -rf "${FROZENTMP}";

mkdir -p "${NGINXLOGDIR}";

# Run rsync checksum on nginx default.conf since other sites might also update
# this file.
mkdir -p "${NGINXDIR}sites-available"
rsync --inplace \
  --checksum \
  --itemize-changes \
  web/default.conf web/puzzle-massive.conf "${NGINXDIR}sites-available/";
echo rsynced web/default.conf web/puzzle-massive.conf to "${NGINXDIR}sites-available/";

mkdir -p "${NGINXDIR}sites-enabled";
ln -sf "${NGINXDIR}sites-available/default.conf" "${NGINXDIR}sites-enabled/default.conf";
ln -sf "${NGINXDIR}sites-available/puzzle-massive.conf"  "${NGINXDIR}sites-enabled/puzzle-massive.conf";

rsync --inplace \
  --checksum \
  --itemize-changes \
  .htpasswd "${SRVDIR}";

if (test -f web/dhparam.pem); then
mkdir -p "${NGINXDIR}ssl/"
rsync --inplace \
  --checksum \
  --itemize-changes \
  web/dhparam.pem "${NGINXDIR}ssl/dhparam.pem";
fi

# Create the root directory for stats. The awstats icons will be placed there.
mkdir -p "${SRVDIR}stats"

if (test -d /usr/share/awstats/icon); then
rsync --archive \
  --inplace \
  --checksum \
  --itemize-changes \
  /usr/share/awstats/icon "${SRVDIR}stats/";
fi

mkdir -p "${AWSTATSLOGDIR}"

# Add crontab file in the cron directory
cp stats/awstats-puzzle-massive-crontab /etc/cron.d/
chmod 0644 /etc/cron.d/awstats-puzzle-massive-crontab
# Stop and start in order for the crontab to be loaded (reload not supported).
systemctl stop cron && systemctl start cron || echo "Can't reload cron service"

# Add the awstats conf
cp stats/awstats.puzzle.massive.xyz.conf /etc/awstats/

# Create the sqlite database file if not there.
if (test ! -f "${DATABASEDIR}db"); then
    echo "Creating database from db.dump.sql"
    mkdir -p "${DATABASEDIR}"
    chown -R dev:dev "${DATABASEDIR}"
    su dev -c "sqlite3 \"${DATABASEDIR}db\" < db.dump.sql"
    # Need to set Write-Ahead Logging so multiple apps can work with the db
    # concurrently.  https://sqlite.org/wal.html
    su dev -c "echo \"pragma journal_mode=wal\" | sqlite3 ${DATABASEDIR}db"
    chmod -R 770 "${DATABASEDIR}"
fi

mkdir -p "${ARCHIVEDIR}"
chown -R dev:dev "${ARCHIVEDIR}"
chmod -R 770 "${ARCHIVEDIR}"

mkdir -p "${CACHEDIR}"
chown -R dev:dev "${CACHEDIR}"
chmod -R 770 "${CACHEDIR}"

mkdir -p "${SYSTEMDDIR}"
cp chill/puzzle-massive-chill.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-chill || echo "can't start service"
systemctl enable puzzle-massive-chill || echo "can't enable service"

cp api/puzzle-massive-api.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-api || echo "can't start service"
systemctl enable puzzle-massive-api || echo "can't enable service"

cp api/puzzle-massive-artist.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-artist || echo "can't start service"
systemctl enable puzzle-massive-artist || echo "can't enable service"

cp api/puzzle-massive-janitor.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-janitor || echo "can't start service"
systemctl enable puzzle-massive-janitor || echo "can't enable service"

cp divulger/puzzle-massive-divulger.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-divulger || echo "can't start service"
systemctl enable puzzle-massive-divulger || echo "can't enable service"

cp api/puzzle-massive-scheduler.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-scheduler || echo "can't start service"
systemctl enable puzzle-massive-scheduler || echo "can't enable service"
