#!/usr/bin/env bash
set -eu -o pipefail

journalctl --follow \
  _SYSTEMD_UNIT=puzzle-massive-chill.service \
  _SYSTEMD_UNIT=puzzle-massive-api.service \
  _SYSTEMD_UNIT=puzzle-massive-artist.service \
  _SYSTEMD_UNIT=puzzle-massive-divulger.service \
  _SYSTEMD_UNIT=puzzle-massive-scheduler.service \
  _SYSTEMD_UNIT=puzzle-massive-cache-purge.path \
  _SYSTEMD_UNIT=puzzle-massive-cache-purge.service \
  _SYSTEMD_UNIT=puzzle-massive-backup-db.timer \
  _SYSTEMD_UNIT=puzzle-massive-backup-db.service \
  _SYSTEMD_UNIT=puzzle-massive-worker.service \
  _SYSTEMD_UNIT=puzzle-massive-publish.service \
  _SYSTEMD_UNIT=puzzle-massive-janitor.service

