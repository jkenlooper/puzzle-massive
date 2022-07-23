#!/usr/bin/env sh

set -o errexit

qc_dir="$(dirname "$(realpath "$0")")"

# TODO set project dir from the quality-control-rc.json file. It should be
# a relative path from the config file.
project_dir="$(dirname "$qc_dir")"

args="$@"

target_directories=". design-tokens/src mockups source-media root enforcer queries stream client-side-public/src docs api chill chill-data divulger documents templates"
test -n "$target_directories"

targets=""
first_target=""
has_top_level="no"
# Allow target_directories to use path expansion. Filter out any that are not
# directories or are outside of the project directory.
for target in $target_directories; do
  test -n "$target" || continue
  rel_path="$(realpath --relative-base="$project_dir" --relative-to="$project_dir" --canonicalize-missing "$target")"
  test "${rel_path##/}" = "$rel_path" || continue
  test -d "$project_dir/$rel_path" || continue
  if [ "$rel_path" = "." ]; then
    has_top_level="yes"
    continue
  fi
  if [ -z "$first_target" ]; then
    first_target="$rel_path"
  else
    targets="$targets $rel_path"
  fi
done
test -n "$first_target"

# Disable pathname expansion so the list of files can use '*' and not have them
# expanded to actual file paths in the for loop.
set -f

file_names="*.js *.jsx *.mjs *.ts *.tsx *.css *.less *.scss *.json *.graphql *.gql *.markdown *.md *.mdown *.mkd *.mkdn *.mdx *.vue *.svelte *.yml *.yaml *.html *.php *.rb *.ruby *.xml *.py"
names=""
first_name=""
for name in $file_names; do
  test -n "$name" || continue
  if [ -z "$first_name" ]; then
    first_name="$name"
  else
    names="$names $name"
  fi
done
test -n "$first_name"

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
set --
if [ -n "$targets" ]; then
  for target in $targets; do
    if [ -n "$target" ]; then
      set -- "$@" "-path" "./$target/*" "-o"
    fi
  done
fi
# Close out the path group with the first target.
set -- "(" "$@" "-path" "$first_target" ")"

set -- "$@" "("
if [ -n "$names" ]; then
  for name in $names; do
    set -- "$@" "-name" "$name" "-o"
  done
fi
# Close out the name group with the first name.
set -- "$@" "-name" "$first_name" ")"

if [ -e "$qc_dir/.formatted-files.tar" ]; then
  set -- "$@" "-newer" "$qc_dir/.formatted-files.tar"
fi

find . \
    -type f -readable -writable \
    "$@" \
    -nowarn \
    -print > "$tmp_file_list"

if [ "$has_top_level" = "yes" ]; then
  set --
  set -- "$@" "("
  if [ -n "$names" ]; then
    for name in $names; do
      set -- "$@" "-name" "$name" "-o"
    done
  fi
  # Close out the name group with the first name.
  set -- "$@" "-name" "$first_name" ")"

  if [ -e "$qc_dir/.formatted-files.tar" ]; then
    set -- "$@" "-newer" "$qc_dir/.formatted-files.tar"
  fi

  find . \
      -depth -maxdepth 1 \
      -type f -readable -writable \
      "$@" \
      -nowarn \
      -print >> "$tmp_file_list"
fi

cat "$tmp_file_list"

if [ -s "$tmp_file_list" ]; then
  rm -f "$qc_dir/.modified-files.tar"
  tar c -f "$qc_dir/.modified-files.tar" \
    -C "$project_dir" \
    --verbatim-files-from \
    --files-from="$tmp_file_list"
else
  echo "No modified files to process that are newer."
fi

set -- $args
make -f "$qc_dir/quality-control.mk" "$@"
