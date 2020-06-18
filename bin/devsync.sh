#!/usr/bin/env bash
set -euo pipefail

which rsync > /dev/null || (echo "No rsync command found. Install rsync." && exit 1)

rsync --archive \
  --itemize-changes \
  --exclude=.git \
  --exclude=.vagrant \
  --exclude=node_modules \
  --exclude=package-lock.json \
  . dev@local-puzzle-massive:/home/dev/puzzle-massive/

