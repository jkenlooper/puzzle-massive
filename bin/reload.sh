#!/usr/bin/env bash
set -eu -o pipefail

printf 'Site down for maintenance. Should be back up in a couple of minutes.' > /srv/puzzle-massive/root/puzzle-massive-message.html;
sudo ./bin/appctl.sh stop;
sudo ./bin/appctl.sh start;
printf '' > /srv/puzzle-massive/root/puzzle-massive-message.html;
