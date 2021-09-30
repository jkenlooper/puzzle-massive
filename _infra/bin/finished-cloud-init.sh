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
Check on the progress of a newly initialized legacy puzzle massive droplet.
"

check_environment_variable $ENVIRONMENT

echo "

Executing Ansible playbook: finished-cloud-init.yml
"

ansible-playbook ansible-playbooks/finished-cloud-init.yml \
 -u dev \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 --limit legacy_puzzle_massive
