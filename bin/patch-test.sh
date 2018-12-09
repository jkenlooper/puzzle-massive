#!/usr/bin/env bash
set -eu -o pipefail

PUZZLEPAGE=$1
DELAY=$2

curl $PUZZLEPAGE -o test.html

PUZZLEID=$(cat test.html | sed --silent -E  's/.*puzzleid="(.*?)".*/\1/p')
WIDTH=$(cat test.html | sed --silent -E  's/style="width:([[:digit:]]+)px; height:([[:digit:]]+)px;"/\1/p')
WIDTH=$(($WIDTH - 100))
HEIGHT=$(cat test.html | sed --silent -E  's/style="width:([[:digit:]]+)px; height:([[:digit:]]+)px;"/\2/p')
HEIGHT=$(($HEIGHT - 100))
PIECECOUNT=$(cat test.html | sed --silent -E  's/([[:digit:]]+) Piece Jigsaw Puzzle.*/\1/p')

echo $PUZZLEID
echo $WIDTH
echo $HEIGHT
echo $PIECECOUNT

while true; do

COUNT=$3;


while test "$COUNT" -gt -1; do

curl --request PATCH \
  --url "http://local-puzzle-massive/newapi/puzzle/${PUZZLEID}/piece/$(shuf -i 1-${PIECECOUNT} -n 1)/move/" \
  --header 'token: 1234abcd' \
  --header 'Referer: http://local-puzzle-massive/' \
  --form x=$(shuf -i 101-${WIDTH} -n 1) \
  --form y=$(shuf -i 101-${HEIGHT} -n 1) \
  -s -S --write-out "%{http_code} %{time_total}\n" \
  -o /dev/null &

COUNT=$(($COUNT-1));

done;

sleep "${DELAY}";


done;

