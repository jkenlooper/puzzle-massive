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
Update the Legacy Puzzle Massive server in-place.
"

check_environment_variable $ENVIRONMENT

echo "

Executing Ansible playbook: in-place-quick-deploy.yml
"

# Prompt for the dist file to use.
versioned_dist_file=puzzle-massive-$(jq -r '.version' ../package.json).tar.gz
latest_dist_file=$(find ../ -maxdepth 1 -name $versioned_dist_file)
example=""
if [ -z "$latest_dist_file" ]; then
  latest_dist_file=$(find ../ -maxdepth 1 -name 'puzzle-massive-*.tar.gz' | head -n1)
  if [ -z "$latest_dist_file" ]; then
    example=' (Create one with the `make dist` command)'
  fi
fi
DIST_FILE=$(read -e -p "
Use dist file:
${example}
" -i "$latest_dist_file" && echo $REPLY)
DIST_FILE=$(realpath $DIST_FILE)
test -e $DIST_FILE || (echo "No file at $DIST_FILE" && exit 1)

ansible-playbook ansible-playbooks/in-place-quick-deploy.yml \
 -u dev \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 --ask-become-pass \
 --extra-vars "message_file=../$ENVIRONMENT/puzzle-massive-message.html
 dist_file=$DIST_FILE
 makeenvironment=$(test $ENVIRONMENT = 'development' && echo 'development' || echo 'production')"
