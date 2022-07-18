#!/usr/bin/env sh

set -o errexit

project_dir="$(dirname "$(dirname "$(realpath "$0")")")"
code_formatter_dir="$(dirname "$(realpath "$0")")"

tmp_file_list="$(mktemp)"
tmp_file_list_dir="$(mktemp -d)"
cleanup() {
  rm -f "$tmp_file_list"
  rm -rf "$tmp_file_list_dir"
}
trap cleanup EXIT

set -- design-tokens/src mockups source-media root enforcer queries stream client-side-public/src docs api chill chill-data divulger documents templates

for target in "$@"; do

  set -- js jsx mjs ts tsx css less scss json graphql gql markdown md mdown mkd mkdn mdx vue svelte yml yaml html php rb ruby xml

  for ext in "$@" py; do
    if [ -e "$code_formatter_dir/.formatted-files.tar" ]; then
      set -- -newer "$code_formatter_dir/.formatted-files.tar"
    else
      set --
    fi
    tmp_name="$(echo "$target-$ext" | sed 's^/^-^g')"
    find . \
        "$@" \
        -type f -readable -writable \
        -path "./$target/*" \
        -name "*.$ext" \
        -nowarn \
        -print >> "$tmp_file_list_dir/$tmp_name" &
  done

done

wait

cat "$tmp_file_list_dir"/* > "$tmp_file_list"

rm -f "$code_formatter_dir/.modified-files.tar"
tar c -f "$code_formatter_dir/.modified-files.tar" \
  -C "$project_dir" \
  --verbatim-files-from \
  --files-from="$tmp_file_list"
