#!/usr/bin/env bash
set -eu -o pipefail

PAGE=$1
DELAY=$2

COUNT=1
while true; do
curl "${PAGE}" -s -S --write-out "%{http_code} %{time_total} ${COUNT}\n" -o /dev/null &
COUNT=$((COUNT+1));
sleep "${DELAY}";
done;

