#!/usr/bin/env bash

# Helper script for using terraform commands in a workspace.
# Don't use this script if doing anything other then mundane main commands like
# plan, apply, or destroy.

set -o nounset
set -o pipefail
set -o errexit

# Should be plan, apply, or destroy
terraform_command=$1

test $(basename $PWD) = "_infra" || (echo "Must run this script from the _infra directory." && exit 1)

# The workspace name is the folder that contains the terra.sh script.
script_dir=$(dirname $(realpath $0))
workspace=$(basename $script_dir)
project_dir=$(dirname $PWD)

tmp_artifact_bundle=$(mktemp -d)/puzzle-massive.bundle

project_description="Temporary instance for development"

echo "Terraform workspace is: $workspace"
echo "Project description will be: '$project_description'"

cd $project_dir
project_version=$(jq -r '.version' package.json)
git diff --quiet || (echo "Project directory is dirty. Please commit any changes first." && exit 1)
git bundle create $tmp_artifact_bundle HEAD
artifact_bundle=puzzle-massive-$project_version.bundle
rm -f puzzle-massive-*.bundle
mv $tmp_artifact_bundle $artifact_bundle
cd -

echo "Versioned artifact bundle file: '$project_dir/$artifact_bundle'"

set -x

rm -f $script_dir/puzzle-massive-*.bundle
cp $project_dir/$artifact_bundle $script_dir/

terraform workspace select $workspace || \
  terraform workspace new $workspace

test "$workspace" = "$(terraform workspace show)" || (echo "Sanity check to make sure workspace selected matches environment has failed." && exit 1)

terraform $terraform_command -var-file="$script_dir/config.tfvars" \
    -var-file="$script_dir/private.tfvars" \
    -var "artifact=$artifact_bundle" \
    -var "project_version=$project_version" \
    -var "project_description=$project_description"
