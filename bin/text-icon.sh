#!/usr/bin/env bash

# Creates a bit-icon from text. Can use emoji or other unicode characters.

set -o pipefail
set -o errexit
set -o nounset

# Lazy way of passing the args.
TEXT=$1
NAME=$2
GROUP=$3

# lowercase
output_file="${NAME,,}"
# replace all spaces with '-' (pattern begins with '/' to match all)
output_file="${output_file// /-}"
# replace all non alphanumeric characters with a '_'
output_file="${output_file//[^[:alnum:]]/_}"

group="${GROUP,,}"
group="${group//[^[:alnum:]]/_}"

# Make text icons using imagemagick and pango:
FONTSIZE=$((512 * 1024))
convert -size 4000x2000 \
  -background transparent \
  -gravity center \
  pango:"<span size='${FONTSIZE}'>${TEXT}</span>" \
  -trim +repage -resize 256x256 -extent 256x256 "bit-icons/${group}-${output_file}.png";
