#!/usr/bin/env bash
set -eu -o pipefail

PAGE=$1
DELAY=$2

while true; do
curl "${PAGE}" -s -S --write-out '%{http_code} %{time_total}\n' -o /dev/null &
sleep "${DELAY}";
done;

