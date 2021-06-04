#!/usr/bin/env bash
set -eu -o pipefail

PROJECT_DIRECTORY=$1

cd $PROJECT_DIRECTORY

watchit src/ && sleep 1 && npm run debug
