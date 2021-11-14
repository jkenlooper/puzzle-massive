#!/usr/bin/env bash

# Use this to run `npm install ...` commands that modify the package.json or
# package-lock.json files.
# Example:
# ./llama.sh npm install --save normalize.css

docker build \
  --target build \
  -t puzzle-massive-client-side-public \
  ./

docker run -it \
  --name puzzle-massive-client-side-public \
  puzzle-massive-client-side-public \
  "$@"

for f in package.json package-lock.json ; do
  docker cp \
    puzzle-massive-client-side-public:/build/$f \
    $f
done

read -e -p "Remove the container? [y/n]
" CONFIRM
if [ "$CONFIRM" == "y" ]; then
  docker rm \
    puzzle-massive-client-side-public
fi
