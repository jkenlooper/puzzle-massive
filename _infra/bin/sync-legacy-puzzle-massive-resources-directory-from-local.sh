#!/usr/bin/env bash

set -o errexit
bin_dir=$(dirname $(realpath $0))
source $bin_dir/common-functions.sh
while getopts ":h" opt; do
  case ${opt} in
    h )
      usage_generic_ansible_playbook;
      ;;
    \? )
      usage_generic_ansible_playbook;
      ;;
  esac;
done;
shift "$((OPTIND-1))";
ENVIRONMENT=${1-$ENVIRONMENT}
test -z "$ENVIRONMENT" && usage_generic_ansible_playbook
set -o nounset

RESOURCES_DIRECTORY=$ENVIRONMENT/resources
RESOURCES_DIRECTORY=$(realpath $RESOURCES_DIRECTORY)
test -d $RESOURCES_DIRECTORY || echo "no directory at $RESOURCES_DIRECTORY"

echo "
Upload the local puzzle resources directory: $RESOURCES_DIRECTORY
to the '$ENVIRONMENT' environment.
"

check_environment_variable $ENVIRONMENT

echo "

Executing Ansible playbook: sync-legacy-puzzle-massive-resources-directory-to-local.yml
"

ansible-playbook ansible-playbooks/sync-legacy-puzzle-massive-resources-directory-from-local.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 -u dev \
 --ask-become-pass \
 --extra-vars "resources_directory=$RESOURCES_DIRECTORY"
