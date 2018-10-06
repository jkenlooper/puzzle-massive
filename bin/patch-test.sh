#!/usr/bin/env bash
set -eu -o pipefail

PUZZLEID=$1
DELAY=$2

while true; do

COUNT=$3;



while test "$COUNT" -gt -1; do

curl --request PATCH \
  --url "http://local-puzzle-massive/newapi/puzzle/${PUZZLEID}/piece/$(shuf -i 1-204 -n 1)/move/" \
  --header 'token: 1234abcd' \
  --header 'Referer: http://local-puzzle-massive/' \
  --form x=$(shuf -i 101-1858 -n 1) \
  --form y=$(shuf -i 101-2500 -n 1) \
  -s -S --write-out "%{http_code} %{time_total}\n" \
  -o /dev/null &

COUNT=$(($COUNT-1));

done;

sleep "${DELAY}";


done;

