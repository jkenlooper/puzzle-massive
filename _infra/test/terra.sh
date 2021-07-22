#!/usr/bin/env bash

# Helper script for using terraform commands in a workspace.
# Don't use this script if doing anything other then mundane main commands like
# console, plan, apply, or destroy.

set -o nounset
set -o pipefail
set -o errexit

# Should be console, plan, apply, or destroy
terraform_command=$1

test $(basename $PWD) = "_infra" || (echo "Must run this script from the _infra directory." && exit 1)

# The workspace name is the folder that contains the terra.sh script.
script_dir=$(dirname $(realpath $0))
workspace=$(basename $script_dir)
project_dir=$(dirname $PWD)

# The test environment is based off of a git tag with test/
test_tag="$(git tag --list 'test/*' --contains)"
test -z $test_tag && echo "Must have a git tag that starts with 'test/' at the HEAD." && exit 1
project_description="Temporary instance for testing based from git tag: $test_tag"

echo "Terraform workspace is: $workspace"
echo "Project description will be: '$project_description'"

cd $project_dir
project_version=$(jq -r '.version' package.json)
artifact_bundle="$(echo puzzle-massive-$project_version-*.bundle)"

if [ ! -e $artifact_bundle -o "${terraform_command}" != "console" ]; then
  git diff --quiet || (echo "Project directory is dirty. Please commit any changes first." && exit 1)
  tmp_artifact_bundle=$(mktemp -d)/puzzle-massive.bundle
  git bundle create $tmp_artifact_bundle HEAD
  artifact_checksum=$(md5sum $tmp_artifact_bundle | cut -f1 -d ' ')
  artifact_bundle=puzzle-massive-$project_version-$artifact_checksum.bundle
  rm -f puzzle-massive-*.bundle
  mv $tmp_artifact_bundle $artifact_bundle
fi

cd -

echo "Versioned artifact bundle file: '$project_dir/$artifact_bundle'"

set -x

existing_artifact="$(echo $script_dir/puzzle-massive-*.bundle)"
if [ ! -e "$existing_artifact" -o "$(md5sum $existing_artifact | cut -f1 -d ' ')" != "$(md5sum $project_dir/$artifact_bundle | cut -f1 -d ' ')" ]; then
  rm -f $script_dir/puzzle-massive-*.bundle
  cp $project_dir/$artifact_bundle $script_dir/
fi

terraform workspace select $workspace || \
  terraform workspace new $workspace

test "$workspace" = "$(terraform workspace show)" || (echo "Sanity check to make sure workspace selected matches environment has failed." && exit 1)

terraform $terraform_command -var-file="$script_dir/config.tfvars" \
    -var-file="$script_dir/private.tfvars" \
    -var "artifact=$artifact_bundle" \
    -var "project_version=$test_tag" \
    -var "project_description=$project_description"
