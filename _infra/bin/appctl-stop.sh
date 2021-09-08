#!/usr/bin/env bash

set -o errexit
set -o nounset

bin_dir=$(dirname $(realpath $0))
source $bin_dir/common-functions.sh

ENVIRONMENT=${1-$ENVIRONMENT}

echo "
Stop the Legacy Puzzle Massive app which will also create the backup database dump file on S3.
"

check_environment_variable $ENVIRONMENT

echo "

Executing Ansible playbook: appctl-stop.yml
"

ansible-playbook ansible-playbooks/appctl-stop.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 --ask-become-pass \
 --extra-vars "message_file=../$ENVIRONMENT/puzzle-massive-message.html"
