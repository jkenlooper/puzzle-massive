#!/usr/bin/env bash

set -o errexit
set -o nounset

bin_dir=$(dirname $(realpath $0))
source $bin_dir/common-functions.sh

ENVIRONMENT=${1-$ENVIRONMENT}

RESOURCES_DIRECTORY=$ENVIRONMENT/resources
RESOURCES_DIRECTORY=$(realpath $RESOURCES_DIRECTORY)
test -d $RESOURCES_DIRECTORY || echo "no directory at $RESOURCES_DIRECTORY"

echo "
Download the puzzle resources directory from '$ENVIRONMENT' environment
to the local directory: $RESOURCES_DIRECTORY
"

check_environment_variable $ENVIRONMENT

echo "

Executing Ansible playbook: sync-legacy-puzzle-massive-resources-directory-to-local.yml
"


ansible-playbook ansible-playbooks/sync-legacy-puzzle-massive-resources-directory-to-local.yml \
  -i $ENVIRONMENT/host_inventory.ansible.cfg \
  --extra-vars "resources_directory=$RESOURCES_DIRECTORY"
