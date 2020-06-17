#!/usr/bin/env bash
set -euo pipefail

rsync --archive \
  --itemize-changes \
  --exclude=.git \
  --exclude=.vagrant \
  --exclude=node_modules \
  --exclude=package-lock.json \
  . dev@local-puzzle-massive:/home/dev/puzzle-massive/

