#!/usr/bin/env sh

set -o errexit

project_dir="$1"
qc_dir="$2"

test -d "$project_dir" || (echo "ERROR $0: First arg should be the project directory" && exit 1)
test -d "$qc_dir" || (echo "ERROR $0: Second arg should be the quality-control directory" && exit 1)

tmp_file_list="$(mktemp)"
cleanup() {
  rm -f "$tmp_file_list"
}
trap cleanup EXIT

# Build up the options that will be passed to the 'find' command by replacing
# the positional parameters in the $@ ( $1 $2 ... ). The '--' is used to prevent
# passing an option to 'set' itself.
set -- "("
for target in design-tokens/src mockups source-media root enforcer queries stream client-side-public/src docs api chill chill-data divulger documents; do
  set -- "$@" "-path" "./$target/*" "-o"
done
# Close out the path group with last item in targets
set -- "$@" "-path" "./templates/*" ")"

set -- "$@" "("
for ext in js jsx mjs ts tsx css less scss json graphql gql markdown md mdown mkd mkdn mdx vue svelte yml yaml html php rb ruby xml; do
  set -- "$@" "-name" "*.$ext" "-o"
done
# Include python file extension last to close out the group.
set -- "$@" "-name" "*.py" ")"

if [ -e "$qc_dir/.formatted-files.tar" ]; then
  set -- "$@" "-newer" "$qc_dir/.formatted-files.tar"
fi

find . \
    -type f -readable -writable \
    "$@" \
    -nowarn \
    -print > "$tmp_file_list"

if [ -s "$tmp_file_list" ]; then
  rm -f "$qc_dir/.modified-files.tar"
  tar c -f "$qc_dir/.modified-files.tar" \
    -C "$project_dir" \
    --verbatim-files-from \
    --files-from="$tmp_file_list"
else
  echo "No modified files to process that are newer."
fi
