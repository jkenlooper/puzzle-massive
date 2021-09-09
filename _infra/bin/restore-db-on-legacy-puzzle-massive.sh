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
Replace the database with a local database dump file.
"

DB_DUMP_FILE=$ENVIRONMENT/db.dump.gz

read -e -p "Enter the path to a db.dump.gz to replace the current sqlite database
with:
" -i "$DB_DUMP_FILE" DB_DUMP_FILE

# Verify that file exists
DB_DUMP_FILE=$(realpath $DB_DUMP_FILE)
test -e $DB_DUMP_FILE || echo "no file at $DB_DUMP_FILE"

check_environment_variable $ENVIRONMENT

echo "

Executing Ansible playbook: restore-db-on-legacy-puzzle-massive.yml
"

ansible-playbook ansible-playbooks/restore-db-on-legacy-puzzle-massive.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 -u dev \
 --ask-become-pass \
 --extra-vars "db_dump_file=$DB_DUMP_FILE"
