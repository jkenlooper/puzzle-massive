test $(basename $PWD) = "_infra" || (echo "Must run this script from the _infra directory." && exit 1)

check_environment_variable () {
  test \
    $1 = 'development' \
    -o $1 = 'test' \
    -o $1 = 'acceptance' \
    -o $1 = 'production' \
    || (echo "environment variable must be either 'development', 'test', 'acceptance', or 'production'. The value '$1' is invalid." && exit 1)

  read -n1 -p "
Execute this script for the '$1' environment?
$1
[y/n] " REPLY

  echo ""
  test $REPLY = "y" || (echo "Cancelled" && exit 1)
}

usage_generic_ansible_playbook () {
  cat <<USAGE
Usage: ${0} [environment]

Executes the script for the environment which generally runs the Ansible
playbook with the same name. Note that the ENVIRONMENT variable can be set and
exported and it will use that if not specifically passed as the first argument
when executing the script.

More documentation on the ${0} script can be found in _infra/README.md document.
Also review the related Ansible playbook:
_infra/ansible-playbooks/$(basename ${0%.sh}.yml)

USAGE
  exit 0;
}
