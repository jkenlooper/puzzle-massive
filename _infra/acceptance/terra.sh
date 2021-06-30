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

artifact_dist_tar_gz=puzzle-massive-$(jq -r '.version' ../package.json).tar.gz
test -e $project_dir/$artifact_dist_tar_gz || (echo "Must create a versioned artifact file at path $project_dir/$artifact_dist_tar_gz before running this command." && exit 1)

project_description="Temporary instance for acceptance"

echo "Terraform workspace is: $workspace"
echo "Project description will be: '$project_description'"
echo "Using versioned artifact dist file: '$project_dir/$artifact_dist_tar_gz'"

set -x

cp $project_dir/$artifact_dist_tar_gz $script_dir/

terraform workspace select $workspace || \
  terraform workspace new $workspace

test "$workspace" = "$(terraform workspace show)" || (echo "Sanity check to make sure workspace selected matches environment has failed." && exit 1)

terraform $terraform_command -var-file="$script_dir/config.tfvars" \
    -var-file="$script_dir/private.tfvars" \
    -var "artifact=$artifact_dist_tar_gz" \
    -var "project_description=$project_description"
