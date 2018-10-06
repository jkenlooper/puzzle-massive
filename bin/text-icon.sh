#!/usr/bin/env bash
set -eu -o pipefail

NAME=$1

# lowercase
output_file="${NAME,,}"
# replace all spaces with '-' (pattern begins with '/' to match all)
output_file="${output_file// /-}"

#make text icons:
convert -size 8000x256 xc:transparent -pointsize 256 -stroke white -strokewidth 5 -gravity center -annotate +0+0 "${NAME}" -trim +repage -resize 256 "${output_file}.png";
