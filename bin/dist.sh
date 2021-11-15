#!/usr/bin/env bash
set -eu -o pipefail

# Create a distribution for uploading to a production server.

# archive file path should be absolute
ARCHIVE=$1

TMPDIR=$(mktemp --directory);

git clone --recurse-submodules . "$TMPDIR";

(
cd "$TMPDIR";
(if [ -d site-specific-content ]; then
  cd site-specific-content
  make
  make install
fi)

cd client-side-public
make
cd -

# Create symlinks for all files in the MANIFEST.
mkdir -p puzzle-massive;
for item in $(cat MANIFEST); do
  dirname "puzzle-massive/${item}" | xargs mkdir -p;
  dirname "puzzle-massive/${item}" | xargs ln -sf "${PWD}/${item}";
done;

# Exclude gimp source files (.xcf)
tar --dereference \
  --exclude=MANIFEST \
  --exclude=*.xcf \
  --create \
  --auto-compress \
  --file "${ARCHIVE}" puzzle-massive;
)

# Clean up
rm -rf "${TMPDIR}";
