#!/usr/bin/env bash
set -eu -o pipefail

# sudo tail -f /var/log/nginx/puzzle-massive/access.log | grep "GET /chill/site/"

PAGE=$1
DELAY=$2

# stop the wget process if ctrl-c
user_stop(){
pkill --newest "wget";
}
trap user_stop SIGINT
trap user_stop SIGTSTP

wget --no-cache \
  --wait=$DELAY \
  --delete-after \
  --no-directories \
  --recursive \
  --reject "*.*" \
  --no-verbose \
  --domains=local-puzzle-massive \
  http://local-puzzle-massive/chill/site/queue/complete/0/ &

COUNT=1
while true; do
curl "${PAGE}" -s -S --write-out "%{http_code} %{time_total} ${COUNT}\n" -o /dev/null &
COUNT=$((COUNT+1));
sleep "${DELAY}";
done;
