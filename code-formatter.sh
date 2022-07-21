#!/usr/bin/env sh

set -o errexit

project_dir="$(dirname "$(realpath "$0")")"
code_formatter_dir="$project_dir/code-formatter"

"$code_formatter_dir/modified-files-manifest.sh" "$project_dir" "$code_formatter_dir"
make -f "$code_formatter_dir/code-formatter.mk" "$@"
