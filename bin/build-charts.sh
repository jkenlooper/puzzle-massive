#!/usr/bin/env bash

# Finds mermaid charts that have been defined in *.md files and creates the svg
# file for each. Will optionally read any associated mermaid config file that is
# next to the markdown file with the same name. For example a markdown file
# named example.md would use example.md.mermaid-config.json file for any extra
# configuration on top of the base mermaid config (docs/mermaid-config.json).

set -o errexit

# Use the image digest to be sure it is the version that is wanted.
# Grab the digest value used:
# docker pull minlag/mermaid-cli:8.13.8
# docker images --filter=reference='minlag/mermaid-cli' --digests
DIGEST="sha256:01e19f589af76ac2564c7088c79fb0f52c311c675f7fb95ad7ee73489b15529e"
MERMAID_CLI="minlag/mermaid-cli@$DIGEST"

# Script directory is bin/
script_dir=$(dirname $(realpath $0))
# Project directory is one level up.
project_dir=$(dirname $script_dir)

BASE_MERMAID_CONFIG=$project_dir/docs/mermaid-config.json

# Change to the project directory so the find command works.
cd $project_dir
echo "Project directory:
$project_dir"
potential_markdown_files=$(find . \
    -type f -name '*.md' \
    -writable -readable \
    ! -path './*.*/*' \
    ! -name '.*' \
    ! -path './*node_modules/*' \
    )
if [ -z "$potential_markdown_files" ]; then
  echo "No markdown files found."
  exit 0
fi

echo "
Searching for mermaid charts in the following files:"
echo "$potential_markdown_files" | sed "s/ /\n/g"
echo ""

targets=$(grep -e '```mermaid' --files-with-matches $potential_markdown_files || printf "")
if [ -z "$targets" ]; then
  echo "No mermaid charts found."
  exit 0
fi

echo "Mermaid charts found in the following files:"
echo "$targets" | sed "s/ /\n/g"
echo ""

for f in $targets; do
  echo ""
  echo "Target file: $f"

  mermaidconfig=$(mktemp)
  if [ -f $f.mermaid-config.json ]; then
    jq --slurp '. | .[0] + .[1]' $BASE_MERMAID_CONFIG $f.mermaid-config.json > $mermaidconfig
  else
    cp $BASE_MERMAID_CONFIG $mermaidconfig
  fi
  echo "Mermaid config:"
  jq . $mermaidconfig

  tmp_dir=$(mktemp -d)
  tmp_container_name=$(basename $tmp_dir)
  cp $f $tmp_dir/

  docker run -it \
    --rm \
    --mount type=bind,src=$mermaidconfig,dst=/tmp/mermaid-config.json,ro \
    --volume=$tmp_dir:/data \
    --user=node \
    $MERMAID_CLI \
    --configFile /tmp/mermaid-config.json \
    --input /data/$(basename $f)

  cp $tmp_dir/*.svg $(dirname $f)/

  # Clean up tmp files
  rm $mermaidconfig
  rm -rf $tmp_dir
done
