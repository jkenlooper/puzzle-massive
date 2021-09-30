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
Add an admin user with a password to be able to access the admin only section
"

check_environment_variable $ENVIRONMENT

# Prompt for the username to use.
BASIC_AUTH_USER=$(read -p 'username: ' && echo $REPLY)

# Prompt for the passphrase to use.
BASIC_AUTH_PASSPHRASE=$(read -sp 'passphrase: ' && echo $REPLY)

echo "

Executing Ansible playbook: add-user-to-basic-auth.yml
"

# Apply the username and passphrase
ansible-playbook ansible-playbooks/add-user-to-basic-auth.yml \
  -i $ENVIRONMENT/host_inventory.ansible.cfg \
  --ask-become-pass \
  --extra-vars "user=$BASIC_AUTH_USER passphrase='$BASIC_AUTH_PASSPHRASE'"
