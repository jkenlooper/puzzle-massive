#!/usr/bin/env bash
set -eu -o pipefail

# Create a distribution for uploading to a production server.

ARCHIVE=$1

# Create symlinks for all files in the MANIFEST.
for item in $(cat puzzle-massive/MANIFEST); do
  dirname "puzzle-massive/${item}" | xargs mkdir -p;
  dirname "puzzle-massive/${item}" | xargs ln -sf "${PWD}/${item}";
done;

tar --dereference \
  --exclude=MANIFEST \
  --create \
  --auto-compress \
  --file "${ARCHIVE}" puzzle-massive;

