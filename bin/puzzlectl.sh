#!/usr/bin/env bash
set -eu -o pipefail

COMMAND=$1

# Simple convenience script to control the apps.

for app in puzzle-massive-chill \
  puzzle-massive-api \
  puzzle-massive-divulger \
  puzzle-massive-artist \
  puzzle-massive-janitor;
do
  echo "";
  echo "systemctl $COMMAND $app;";
  echo "----------------------------------------";
  systemctl "$COMMAND" "$app" | cat;
done;

