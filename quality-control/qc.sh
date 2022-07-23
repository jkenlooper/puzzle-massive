#!/usr/bin/env sh

set -o errexit

usage() {
  cat <<HERE
Quality Control script to show issues with code as well as reformat it.

Uses eslint, stylelint, prettier, black.

Can optionally take a target argument which will be passed to the quality
control makefile.

Usage:
  $script_name -h
  $script_name
  $script_name <target>

Options:
  -h                Show this help message.

Targets:
  lint-auto-fix   - Run the linting tools with auto-fix option.
  clean           - Removes any generated tar files that were made.

HERE
}

qc_dir="$(dirname "$(realpath "$0")")"
script_name="$(basename "$0")"
rc_file_name=".quality-control-rc.json"

# These defaults can be overridden by the values in the rc file.

# The project directory is usually one directory up from the quality control
# directory.
project_dir="$(dirname "$qc_dir")"

# Default to all top level directories and files of the project.
# The "." is used for including top level files.
# The "*" will expand to all directory names at the top level.
target_directories=". *"

# Exclude any directories that are node_modules and .git
exclude_paths="./*node_modules/* ./*.git/*"

# Only include the file names with these extensions which prettier and black
# will typically format.
file_names="*.js *.jsx *.mjs *.ts *.tsx *.css *.less *.scss *.json *.graphql *.gql *.markdown *.md *.mdown *.mkd *.mkdn *.mdx *.vue *.svelte *.yml *.yaml *.html *.php *.rb *.ruby *.xml *.py"

tmp_file_list="$(mktemp)"
cleanup() {
  rm -f "$tmp_file_list"
}
trap cleanup EXIT

find_and_load_run_command_file() {
  rc_file=""
  find_dir="$qc_dir"
  while [ -z "$rc_file" ]; do
    rc_file="$(find "$find_dir" \
      -depth -maxdepth 1 \
      -type f \
      -name "$rc_file_name")"
    find_dir="$(dirname "$find_dir")"
    if [ "$find_dir" = "/" ]; then
      break
    fi
  done
  if [ -z "$rc_file" ]; then
    echo "WARNING $script_name: No run command configuration file with the name '$rc_file_name' found in the directory $qc_dir and it's parent directories." >&2
    echo "Using default values."
  else

    # Fallback on default values if none are found in the rc file.
    rc_project_dir="$(jq -r '@sh "\(.project_dir // "")"' "$rc_file" | xargs)"
    project_dir="${rc_project_dir:-$project_dir}"

    rc_target_directories="$(jq -r '@sh "\(.target_directories // [])"' "$rc_file" | xargs)"
    target_directories="${rc_target_directories:-$target_directories}"

    rc_exclude_paths="$(jq -r '@sh "\(.exclude_paths // [])"' "$rc_file" | xargs)"
    exclude_paths="${rc_exclude_paths:-$exclude_paths}"

    rc_file_names="$(jq -r '@sh "\(.file_names // [])"' "$rc_file" | xargs)"
    file_names="${rc_file_names:-$file_names}"

    # Always want the project_dir to be absolute.
    if [ "${project_dir#/}" = "$project_dir" ]; then
      rc_dir="$(dirname "$rc_file")"
      project_dir="$(realpath "$rc_dir/$project_dir")"
    fi
  fi

  # Validate
  test -d "$project_dir" || (echo "ERROR $script_name: The project directory '$project_dir' is not a directory" >&2 && exit 1)
  test -n "$target_directories" || (echo "ERROR $script_name: The target_directories value is empty." >&2 && exit 1)
  test -n "$file_names" || (echo "ERROR $script_name: The file_names value is empty." >&2 && exit 1)
}

create_modified_files_tar() {
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

  not_paths=""
  first_not_path=""
  for not_path in $exclude_paths; do
    test -n "$not_path" || continue
    if [ -z "$first_not_path" ]; then
      first_not_path="$not_path"
    else
      not_paths="$not_paths $not_path"
    fi
  done

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
  set -- "(" "$@" "-path" "./$first_target/*" ")"

  if [ -n "$first_not_path" ]; then
    set -- "$@" "!" "("
    if [ -n "$not_paths" ]; then
      for not_path in $not_paths; do
        set -- "$@" "-path" "$not_path" "-o"
      done
    fi
    # Close out the not paths group with the first not path.
    set -- "$@" "-path" "$first_not_path" ")"
  fi

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

  if [ -s "$tmp_file_list" ]; then
    rm -f "$qc_dir/.modified-files.tar"
    tar c -f "$qc_dir/.modified-files.tar" \
      -C "$project_dir" \
      --verbatim-files-from \
      --files-from="$tmp_file_list"
  else
    echo "No modified files to process that are newer."
  fi
}

run_qc_makefile() {
  set -- $args
  make --directory="$project_dir" -f "$qc_dir/quality-control.mk" "$@"
}

while getopts "h" OPTION ; do
  case "$OPTION" in
    h) usage
      exit 0 ;;
    ?) usage
      exit 1 ;;
  esac
done
shift $((OPTIND - 1))

# Preserve the args passed in so they can be sent to the makefile.
args="$@"

# Set the working directory to the project dir so the find command works.
cd "$project_dir"

find_and_load_run_command_file
create_modified_files_tar
run_qc_makefile
