#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

usage () {
  cat <<USAGE
Usage: ${0} [-h] [environment]

Options:
  -h            Show help

Deployment using Terraform for the environment that was passed in as the first
arg.  This command will wait for DNS TTL to timeout when making changes. During
the deployment you will be prompted to edit the Terraform variables:

- is_swap_a_active
- is_swap_b_active
- create_legacy_puzzle_massive_swap_a
- create_legacy_puzzle_massive_swap_b

These variables should be set in a _infra/[environment]/private.tfvars file.

USAGE
  exit 0;
}

while getopts ":h" opt; do
  case ${opt} in
    h )
      usage;
      ;;
    \? )
      usage;
      ;;
  esac;
done;
shift "$((OPTIND-1))";

ENVIRONMENT=$1

wait_until_dns_ttl_timeout () {
  echo "Waiting $1 seconds for DNS TTL to timeout."
  sleep $1
  # 64 is the max number of hops a linux system will typically have before it drops the packet.
  echo "Waiting another 64 more seconds to ensure DNS has been fully propagated."
  sleep 64
}

test $(basename $PWD) = "_infra" || (echo "Must run this script from the _infra directory." && exit 1)
test -e $ENVIRONMENT/terra.sh || (echo "No terra.sh found in _infra/$ENVIRONMENT/ directory." && exit 1)
test -e $ENVIRONMENT/private.tfvars || (echo "No terraform private variables file found at $ENVIRONMENT/private.tfvars" && exit 1)

# Check to see if the terraform variables can be modified via setting TF_VAR_*
# environment variables.
TERRAFORM_VARIABLE_NOT_MODIFIABLE_MESSAGE='
The $0 script relies on being able to temporarily set some terraform environment
variables.  These variables should not be set in your .tfvars files as they
would not be able to be overridden by the TF_VAR_* environment variable that this
script temporarily uses.
'

for modifiable_variable in is_floating_ip_active create_floating_ip_puzzle_massive use_short_dns_ttl ; do
  echo $modifiable_variable
  TEST_var=$(echo "var.$modifiable_variable" | \
    ./$ENVIRONMENT/terra.sh console 2> /dev/null | tail -n1)
  test "${TEST_var}" = "false" || (echo "Incompatible state of $modifiable_variable terraform variable. $TERRAFORM_VARIABLE_NOT_MODIFIABLE_MESSAGE" && exit 1)
  TEST_var=$(echo "var.$modifiable_variable" | \
    TF_VAR_is_floating_ip_active=true \
    TF_VAR_create_floating_ip_puzzle_massive=true \
    TF_VAR_use_short_dns_ttl=true \
    ./$ENVIRONMENT/terra.sh console 2> /dev/null | tail -n1)
  test "$TEST_var" = "true" || (echo "Incompatible state of $modifiable_variable terraform variable. $TERRAFORM_VARIABLE_NOT_MODIFIABLE_MESSAGE" && exit 1)
done


# Set a local variable for the Fully Qualified Domain Name to what has been set
# for the Terraform variables 'sub_domain' and 'domain' for this environment. The
# ENVIRONMENT variable should be a valid environment like 'development', 'test',
# 'acceptance', or 'production'.

FQDN=$(echo 'format("${var.sub_domain}${var.domain}")' | \
  ./$ENVIRONMENT/terra.sh console 2> /dev/null | tail -n1 | xargs)
echo "The FQDN for the $ENVIRONMENT environment is $FQDN."

SHORTER_DNS_TTL=$(echo 'var.short_dns_ttl' | \
  ./$ENVIRONMENT/terra.sh console 2> /dev/null | tail -n1)

# Get the current DNS TTL.

CURRENT_DNS_TTL=$(dig +nocmd @ns1.digitalocean.com $FQDN +noall +answer | cut -f2)
echo "Current DNS TTL is $CURRENT_DNS_TTL seconds for $FQDN."



# TODO: It may be better to generate a script here of the rest of the commands
# to run. That way it could be modified as needed for a deployment or used as
# a guide when doing a deployment.  Otherwise if some command failed it might be
# hard to pick up where it was left off since running all these commands again
# are not idempotent.

echo "WIP and not fully implemented.  Exiting out now."
exit 0



# 1. Update DNS TTL to be shorter
TF_VAR_use_short_dns_ttl=true \
./$ENVIRONMENT/terra.sh apply

echo "Waiting for new shorter DNS TTL to be set."
while [ $COUNT -le 10 ]; do
  if [ $(dig +nocmd @ns1.digitalocean.com $FQDN +noall +answer | cut -f2) -ne $SHORTER_DNS_TTL ]; then
    COUNT=$(($COUNT+1));
    sleep 10
    printf "."
  else
    # exit out
    COUNT=11
  fi
done

# 2. Wait until after DNS propagates (depending on previous TTL value)
wait_until_dns_ttl_timeout $CURRENT_DNS_TTL


# 3. Add DO floating IP and point to the legacy puzzle massive droplet swap_a or swap_b that is active
TF_VAR_use_short_dns_ttl=true \
TF_VAR_create_floating_ip_puzzle_massive=true \
TF_VAR_is_floating_ip_active=true \
./$ENVIRONMENT/terra.sh apply


# 4. Wait until after DNS propagates (depending on shorter TTL value)
wait_until_dns_ttl_timeout $SHORTER_DNS_TTL

# 5. Create the new swap for legacy puzzle massive droplet and verify
# Create both swaps here. Only the active swap will be getting traffic since the floating ip will be pointing to it.
read -p "Update the create_legacy_puzzle_massive_swap_a and create_legacy_puzzle_massive_swap_b in the _infra/$ENVIRONMENT/private.tfvars file.
Set create_legacy_puzzle_massive_swap_a = true
Set create_legacy_puzzle_massive_swap_b = true
Continue? [y/n] " -n1 CONFIRM
if [ $CONFIRM != "y" ]; then
  echo "Cancelled deployment."
  exit 0
fi

TF_VAR_use_short_dns_ttl=true \
TF_VAR_create_floating_ip_puzzle_massive=true \
TF_VAR_is_floating_ip_active=true \
./$ENVIRONMENT/terra.sh apply

# TODO: run Ansible playbook to stop active swap and create backup.
# TODO: run Ansible playbook to setup new swap with backup data from active swap.

# TODO: Include ip address to new swap in order to validate.
read -p "Verify that new swap is working correctly. [y/n] " -n1 CONFIRM
if [ $CONFIRM != "y" ]; then
  echo "Cancelled deployment. Active swap is currently stopped still."
  exit 0
fi

read -p "Update the is_swap_a_active and is_swap_b_active in the _infra/$ENVIRONMENT/private.tfvars file. Continue? [y/n] " -n1 CONFIRM
if [ $CONFIRM != "y" ]; then
  echo "Cancelled deployment. Active swap is currently stopped still."
  exit 0
fi

# 6. Update floating IP to point to new swap
TF_VAR_use_short_dns_ttl=true \
TF_VAR_create_floating_ip_puzzle_massive=true \
TF_VAR_is_floating_ip_active=true ./$ENVIRONMENT/terra.sh apply

read -p "New swap is now active. Continue with cleaning up old swap? [y/n] " -n1 CONFIRM
if [ $CONFIRM != "y" ]; then
  echo "Cancelled deployment. Old swap is currently stopped and not active."
  exit 0
fi

# 7. Remove old swap if everything is looking good
read -p "Update the create_legacy_puzzle_massive_swap_a and create_legacy_puzzle_massive_swap_b in the _infra/$ENVIRONMENT/private.tfvars file. Continue? [y/n] " -n1 CONFIRM
if [ $CONFIRM != "y" ]; then
  echo "Cancelled deployment. Old swap is currently stopped and not active."
  exit 0
fi

# 8. Update DNS to point to new swap instead of floating IP
TF_VAR_use_short_dns_ttl=true \
TF_VAR_create_floating_ip_puzzle_massive=true \
TF_VAR_is_floating_ip_active=false ./$ENVIRONMENT/terra.sh apply

# 9. Wait until after DNS propagates (depending on previous TTL value)
wait_until_dns_ttl_timeout $SHORTER_DNS_TTL

# 10. Remove DO floating IP
# TODO: Might be safer to do this last?
TF_VAR_use_short_dns_ttl=true \
TF_VAR_create_floating_ip_puzzle_massive=false ./$ENVIRONMENT/terra.sh apply


# 11. Update DNS TTL to be the longer value that was originally used.
./$ENVIRONMENT/terra.sh apply
