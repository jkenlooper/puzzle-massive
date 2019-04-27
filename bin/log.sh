#!/usr/bin/env bash
set -eu -o pipefail

journalctl --follow \
  _SYSTEMD_UNIT=puzzle-massive-chill.service \
  _SYSTEMD_UNIT=puzzle-massive-api.service \
  _SYSTEMD_UNIT=puzzle-massive-artist.service \
  _SYSTEMD_UNIT=puzzle-massive-divulger.service \
  _SYSTEMD_UNIT=puzzle-massive-scheduler.service \
  _SYSTEMD_UNIT=puzzle-massive-janitor.service

