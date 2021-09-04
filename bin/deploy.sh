#!/usr/bin/env bash
set -eu -o pipefail

echo "Deprecated. Do not use."
exit 1

# TODO: add usage help

FROZENTMP=$(mktemp -d);
tar --directory="${FROZENTMP}" --gunzip --extract -f frozen.tar.gz

# TODO: add bucket if not exist

# Prompt to execute the aws s3 commands
echo aws s3 sync \
  "${FROZENTMP}/frozen/" s3://puzzle.massive.xyz/ \
  --profile puzzle-massive \
  $@
echo aws s3 sync \
  root/ s3://puzzle.massive.xyz/ \
  --profile puzzle-massive \
  $@
read -p "execute commands? y/n " -n 1 CONTINUE

# Execute the aws s3 commands
if test $CONTINUE == 'y'; then
aws s3 sync \
  "${FROZENTMP}/frozen/" s3://puzzle.massive.xyz/ \
  --profile puzzle-massive \
  $@
aws s3 sync \
  root/ s3://puzzle.massive.xyz/ \
  --profile puzzle-massive \
  $@
fi

rm -rf "${FROZENTMP}";
