#!/usr/bin/env bash
set -eu -o pipefail

ENVIRONMENT=$1

# /srv/puzzle-massive/
SRVDIR=$2

# /etc/nginx/
NGINXDIR=$3

# /var/log/nginx/puzzle-massive/
NGINXLOGDIR=$4

# /var/log/awstats/puzzle-massive/
AWSTATSLOGDIR=$5

# /etc/systemd/system/
SYSTEMDDIR=$6

# All processes using a database must be on the same host computer; WAL does not
# work over a network filesystem. If using Vagrant, the db file can't be in
# a shared directory.
# /var/lib/puzzle-massive/sqlite3/
DATABASEDIR=$7

# /var/lib/puzzle-massive/archive/
ARCHIVEDIR=$8

# /var/lib/puzzle-massive/cache/
CACHEDIR=$9

# /var/lib/puzzle-massive/urls-to-purge.txt
PURGEURLLIST=${10}

IMAGEMAGICK_POLICY=${11}

#/etc/ImageMagick-6/policy.xml
#resources/imagemagick-policy.xml;

mkdir -p "${SRVDIR}root/";
#chown -R dev:dev "${SRVDIR}root/";
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

if test "${ENVIRONMENT}" != 'development'; then
mkdir -p "${SRVDIR}dist/";
mkdir -p "${SRVDIR}media/";
chown -R dev:dev "${SRVDIR}dist/";
chown -R dev:dev "${SRVDIR}media/";
rsync --archive \
  --inplace \
  --delete \
  --itemize-changes \
  dist/ "${SRVDIR}dist/";
echo "rsynced files in dist to ${SRVDIR}dist/";
rsync --archive \
  --inplace \
  --delete \
  --exclude=bit-icons \
  --itemize-changes \
  media/ "${SRVDIR}media/";
echo "rsynced files in media to ${SRVDIR}media/";
fi

mkdir -p "${NGINXLOGDIR}";

# Run rsync checksum on nginx default.conf since other sites might also update
# this file.
mkdir -p "${NGINXDIR}sites-available"
rsync --inplace \
  --checksum \
  --itemize-changes \
  web/default.conf web/puzzle-massive.conf web/puzzle-massive--down.conf "${NGINXDIR}sites-available/";
echo rsynced web/default.conf web/puzzle-massive.conf web/puzzle-massive--down.conf to "${NGINXDIR}sites-available/";

mkdir -p "${NGINXDIR}sites-enabled";
ln -sf "${NGINXDIR}sites-available/default.conf" "${NGINXDIR}sites-enabled/default.conf";

rm -f "${NGINXDIR}sites-enabled/puzzle-massive--down.conf"
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
if (test -f web/local-puzzle-massive.crt); then
mkdir -p "${NGINXDIR}ssl/"
rsync --inplace \
  --checksum \
  --itemize-changes \
  web/local-puzzle-massive.crt "${NGINXDIR}ssl/local-puzzle-massive.crt";
fi
if (test -f web/local-puzzle-massive.key); then
mkdir -p "${NGINXDIR}ssl/"
rsync --inplace \
  --checksum \
  --itemize-changes \
  web/local-puzzle-massive.key "${NGINXDIR}ssl/local-puzzle-massive.key";
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

# Set the sqlite database file from the db.dump.sql.
echo "Setting Chill database tables from db.dump.sql"
mkdir -p "${DATABASEDIR}"
chown -R dev:dev "${DATABASEDIR}"
su dev -c "sqlite3 \"${DATABASEDIR}db\" < db.dump.sql"
# Need to set Write-Ahead Logging so multiple apps can work with the db
# concurrently.  https://sqlite.org/wal.html
su dev -c "echo \"pragma journal_mode=wal\" | sqlite3 ${DATABASEDIR}db"
chmod -R 770 "${DATABASEDIR}"

mkdir -p "${ARCHIVEDIR}"
chown -R dev:dev "${ARCHIVEDIR}"
chmod -R 770 "${ARCHIVEDIR}"

mkdir -p "${CACHEDIR}"
chown -R www-data:www-data "${CACHEDIR}"
chmod -R 770 "${CACHEDIR}"

mkdir -p $(dirname ${PURGEURLLIST})
chown dev:www-data -R $(dirname ${PURGEURLLIST})
chmod 0770 $(dirname ${PURGEURLLIST})
touch ${PURGEURLLIST}

# Rename any existing policy.xml file before overwritting it.
mkdir -p $(dirname ${IMAGEMAGICK_POLICY})
touch ${IMAGEMAGICK_POLICY}
if test ! -f ${IMAGEMAGICK_POLICY}.bak; then
mv ${IMAGEMAGICK_POLICY} ${IMAGEMAGICK_POLICY}.bak
fi
cp resources/imagemagick-policy.xml ${IMAGEMAGICK_POLICY}

mkdir -p "${SYSTEMDDIR}"
cp chill/puzzle-massive-chill.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-chill || echo "can't start service"
systemctl enable puzzle-massive-chill || echo "can't enable service"

cp api/puzzle-massive-api.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-api || echo "can't start service"
systemctl enable puzzle-massive-api || echo "can't enable service"

cp api/puzzle-massive-publish.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-publish || echo "can't start service"
systemctl enable puzzle-massive-publish || echo "can't enable service"

cp api/puzzle-massive-artist.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-artist || echo "can't start service"
systemctl enable puzzle-massive-artist || echo "can't enable service"

cp api/puzzle-massive-janitor.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-janitor || echo "can't start service"
systemctl enable puzzle-massive-janitor || echo "can't enable service"

cp api/puzzle-massive-worker.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-worker || echo "can't start service"
systemctl enable puzzle-massive-worker || echo "can't enable service"

# Skipping divulger since it is not needed at the moment.
#cp divulger/puzzle-massive-divulger.service "${SYSTEMDDIR}"
#systemctl start puzzle-massive-divulger || echo "can't start service"
#systemctl enable puzzle-massive-divulger || echo "can't enable service"

cp stream/puzzle-massive-stream.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-stream || echo "can't start service"
systemctl enable puzzle-massive-stream || echo "can't enable service"

cp api/puzzle-massive-scheduler.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-scheduler || echo "can't start service"
systemctl enable puzzle-massive-scheduler || echo "can't enable service"

cp api/puzzle-massive-cache-purge.path "${SYSTEMDDIR}"
cp api/puzzle-massive-cache-purge.service "${SYSTEMDDIR}"
systemctl start puzzle-massive-cache-purge.path || echo "can't start service"
systemctl enable puzzle-massive-cache-purge.path || echo "can't enable service"
systemctl start puzzle-massive-cache-purge.service || echo "can't start service"
systemctl enable puzzle-massive-cache-purge.service || echo "can't enable service"

cp api/puzzle-massive-backup-db.service "${SYSTEMDDIR}"
cp api/puzzle-massive-backup-db.timer "${SYSTEMDDIR}"
systemctl start puzzle-massive-backup-db.timer || echo "can't start service"
systemctl enable puzzle-massive-backup-db.timer || echo "can't enable service"
systemctl start puzzle-massive-backup-db.service || echo "can't start service"
systemctl enable puzzle-massive-backup-db.service || echo "can't enable service"
