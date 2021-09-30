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

echo "
Start the Legacy Puzzle Massive app.
"

check_environment_variable $ENVIRONMENT

echo "

Executing Ansible playbook: appctl-start.yml
"

ansible-playbook ansible-playbooks/appctl-start.yml \
  -i $ENVIRONMENT/host_inventory.ansible.cfg \
  --ask-become-pass
