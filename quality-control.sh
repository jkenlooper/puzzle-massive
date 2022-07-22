#!/usr/bin/env sh

set -o errexit

project_dir="$(dirname "$(realpath "$0")")"
quality_control_dir="$project_dir/quality-control"

"$quality_control_dir/modified-files-manifest.sh" "$project_dir" "$quality_control_dir"
make -f "$quality_control_dir/quality-control.mk" "$@"
