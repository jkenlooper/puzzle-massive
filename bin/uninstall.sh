#!/usr/bin/env bash

set -eu -o pipefail
shopt -s extglob

# Uninstall and clean up script

# /srv/puzzle-massive/
SRVDIR=$1

# /etc/nginx/
NGINXDIR=$2

# /etc/systemd/system/
SYSTEMDDIR=$3

# /var/lib/puzzle-massive/sqlite3/
DATABASEDIR=$4

# /var/lib/puzzle-massive/archive/
ARCHIVEDIR=$5

# /var/lib/puzzle-massive/cache/
CACHEDIR=$6

# /var/lib/puzzle-massive/urls-to-purge.txt
PURGEURLLIST=${10}

rm -rf ${SRVDIR}root/!(.well-known|.|..)

rm -rf "${SRVDIR}frozen/"
rm -rf "${SRVDIR}dist/"
rm -rf "${SRVDIR}media/"

rm -f "${NGINXDIR}sites-enabled/puzzle-massive.conf";
rm -f "${NGINXDIR}sites-available/puzzle-massive.conf";

rm -f "${SRVDIR}.htpasswd";

rm -f /etc/cron.d/awstats-puzzle-massive-crontab
# Stop and start in order for the crontab to be loaded (reload not supported).
systemctl stop cron && systemctl start cron || echo "Can't reload cron service"

rm -f /etc/awstats/awstats.puzzle.massive.xyz.conf

systemctl stop puzzle-massive-chill
systemctl disable puzzle-massive-chill
rm -f "${SYSTEMDDIR}puzzle-massive-chill.service";

systemctl stop puzzle-massive-api
systemctl disable puzzle-massive-api
rm -f "${SYSTEMDDIR}puzzle-massive-api.service";

systemctl stop puzzle-massive-artist
systemctl disable puzzle-massive-artist
rm -f "${SYSTEMDDIR}puzzle-massive-artist.service";

systemctl stop puzzle-massive-janitor
systemctl disable puzzle-massive-janitor
rm -f "${SYSTEMDDIR}puzzle-massive-janitor.service";

systemctl stop puzzle-massive-scheduler
systemctl disable puzzle-massive-scheduler
rm -f "${SYSTEMDDIR}puzzle-massive-scheduler.service";

systemctl stop puzzle-massive-cache-purge.service
systemctl disable puzzle-massive-cache-purge.service
systemctl stop puzzle-massive-cache-purge.path
systemctl disable puzzle-massive-cache-purge.path
rm -f "${SYSTEMDDIR}puzzle-massive-cache-purge.service";
rm -f "${SYSTEMDDIR}puzzle-massive-cache-purge.path";

systemctl stop puzzle-massive-backup-db.service
systemctl disable puzzle-massive-backup-db.service
systemctl stop puzzle-massive-backup-db.timer
systemctl disable puzzle-massive-backup-db.timer
rm -f "${SYSTEMDDIR}puzzle-massive-backup-db.service";
rm -f "${SYSTEMDDIR}puzzle-massive-backup-db.timer";

# TODO: Should it remove the database file in an uninstall?
echo "Skipping removal of sqlite database file ${DATABASEDIR}db"
#rm -f "${DATABASEDIR}db"

rm -rf "${ARCHIVEDIR}"

rm -rf "${CACHEDIR}"

rm -f "${PURGEURLLIST}"

exit
