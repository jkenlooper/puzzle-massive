#!/usr/bin/env bash

set -o errexit
set -o nounset

bin_dir=$(dirname $(realpath $0))
source $bin_dir/common-functions.sh

ENVIRONMENT=${1-$ENVIRONMENT}

echo "
This will run an apt-get update and reboot the machine.
"

check_environment_variable $ENVIRONMENT

echo "

Executing Ansible playbook: update-packages-and-reboot.yml
"

ansible-playbook ansible-playbooks/update-packages-and-reboot.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 --ask-become-pass \
 --extra-vars "message_file=../$ENVIRONMENT/puzzle-massive-message.html"
