#!/usr/bin/env bash
set -eu -o pipefail

PUZZLEID=$1
DELAY=$2

while true; do

COUNT=$3;

while test $COUNT -gt -1; do

curl --request GET \
  --url "http://local-puzzle-massive/newapi/puzzle-pieces/${PUZZLEID}/" \
  --header 'cache-control: no-cache' \
  --header 'token: 1234abcd' \
  --header 'Referer: http://local-puzzle-massive/' \
  -s -S --write-out "%{http_code} %{time_total}\n" \
  -o /dev/null &

COUNT=$(($COUNT-1));

done;

sleep "${DELAY}";


done;

