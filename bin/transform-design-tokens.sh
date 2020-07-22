#!/usr/bin/env bash
set -eu -o pipefail

# TODO: this could be a Makefile

theo design-tokens/default-theme/settings.yaml \
  --setup src/lib/custom-properties-selector.cjs \
  --transform web \
  --format custom-properties-selector.css \
  --dest .design-tokens-css/default-theme

theo design-tokens/dark-theme/settings.yaml \
  --setup src/lib/custom-properties-selector.cjs \
  --transform web \
  --format custom-properties-selector.css \
  --dest .design-tokens-css/dark-theme
