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
Stop the Legacy Puzzle Massive app which will also create the backup database dump file on S3.
Make and make install and reload NGINX.
"

check_environment_variable $ENVIRONMENT

echo "
Executing Ansible playbook: appctl-stop.yml
"

ansible-playbook ansible-playbooks/appctl-stop.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 --ask-become-pass \
 --extra-vars "message_file=../$ENVIRONMENT/puzzle-massive-message.html"

echo "
Executing Ansible playbook: make-install-and-reload-nginx.yml
"

ansible-playbook ansible-playbooks/make-install-and-reload-nginx.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 --ask-become-pass \
 --extra-vars "message_file=../$ENVIRONMENT/puzzle-massive-message.html"
