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

echo "Verify that the file exists and is correct"
ALLOW_DENY_ADMIN_NGINX_CONF=$(realpath $ENVIRONMENT/allow_deny_admin.nginx.conf)
test -e $ALLOW_DENY_ADMIN_NGINX_CONF || echo "no file at $ALLOW_DENY_ADMIN_NGINX_CONF"

echo "Contents of $ENVIRONMENT/allow_deny_admin.nginx.conf
---

"
cat $ALLOW_DENY_ADMIN_NGINX_CONF

echo "
---
"


echo "
Upload local file $ENVIRONMENT/allow_deny_admin.nginx.conf and reload NGINX
"

check_environment_variable $ENVIRONMENT


echo "

Executing Ansible playbook: update-allow_deny_admin_nginx_conf.yml
"

# Apply the new allow_deny_admin.nginx.conf file
ansible-playbook ansible-playbooks/update-allow_deny_admin_nginx_conf.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 --ask-become-pass \
 --extra-vars "allow_deny_admin_nginx_conf=$ALLOW_DENY_ADMIN_NGINX_CONF"
