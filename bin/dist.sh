#!/usr/bin/env bash
set -eu -o pipefail

# Create a distribution for uploading to a production server.

ARCHIVE=$1

TMPDIR=$(mktemp --directory);
#SOURCEDIR=$(pwd);

git clone . "$TMPDIR";
cd "$TMPDIR";

# Build
(
cd puzzle-pieces;
npm install; # or `npm ci` ?
npm pack;
mv puzzle-pieces-*.tgz ../ui-lib/;
)


# Create symlinks for all files in the MANIFEST.
for item in $(cat puzzle-massive/MANIFEST); do
  dirname "puzzle-massive/${item}" | xargs mkdir -p;
  dirname "puzzle-massive/${item}" | xargs ln -sf "${PWD}/${item}";
done;

tar --dereference \
  --exclude=MANIFEST \
  --exclude=*.pyc \
  --create \
  --auto-compress \
  --file "${ARCHIVE}" puzzle-massive;

