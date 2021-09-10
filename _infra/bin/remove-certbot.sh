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
Remove certbot auto renewal process and delete the provisioned certificate for the domain.
"

check_environment_variable $ENVIRONMENT

echo "

Executing Ansible playbook: remove-certbot.yml
"

ansible-playbook ansible-playbooks/remove-certbot.yml \
 --ask-become-pass \
 -i $ENVIRONMENT/host_inventory.ansible.cfg
