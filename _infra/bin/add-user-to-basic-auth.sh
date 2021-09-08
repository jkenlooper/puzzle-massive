#!/usr/bin/env bash

set -o errexit
set -o nounset

bin_dir=$(dirname $(realpath $0))
source $bin_dir/common-functions.sh

ENVIRONMENT=${1-$ENVIRONMENT}

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
