#!/usr/bin/env sh
set -eu -o pipefail

rm -rf tmp/
mkdir -p tmp/

theo src/default-theme/settings.yaml \
  --setup custom-properties-selector.cjs \
  --transform web \
  --format custom-properties-selector.css \
  --dest tmp/default-theme

theo src/dark-theme/settings.yaml \
  --setup custom-properties-selector.cjs \
  --transform web \
  --format custom-properties-selector.css \
  --dest tmp/dark-theme
