#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

usage () {
  cat <<USAGE
Usage: ${0} [environment]
       ${0} -s <step number> [environment]
       ${0} -h

Options:
  -h            Show help
  -s STEP       Skip to step number

Deployment using Terraform for the environment that was passed in as the first
arg.  This command will wait for DNS TTL to timeout when making changes. During
the deployment you will be prompted to edit the Terraform variables:

- old_swap
- new_swap
- is_swap_a_active
- is_swap_b_active
- create_legacy_puzzle_massive_swap_a
- create_legacy_puzzle_massive_swap_b

These variables should be set in a _infra/[environment]/private.tfvars file.

There are multiple steps in this deployment script. The last successful step is
saved locally and may be skipped to.

More information for this script is in the _infra/README.md document.

USAGE
  exit 0;
}


STEP_STATE=1
while getopts ":hs:" opt; do
  case ${opt} in
    s )
      STEP_STATE=${OPTARG}
      ;;
    h )
      usage;
      ;;
    \? )
      usage;
      ;;
  esac;
done;
shift "$((OPTIND-1))";

bin_dir=$(dirname $(realpath $0))
source $bin_dir/common-functions.sh

ENVIRONMENT=${1-$ENVIRONMENT}

# Only Acceptance and Production will be publicly available so provisioning
# certs would then be done.
PROVISION_CERTS=$(test "$ENVIRONMENT" = "acceptance" -o "$ENVIRONMENT" = "production" && echo "1" || echo "0")

test -e $ENVIRONMENT/terra.sh || (echo "No terra.sh found in _infra/$ENVIRONMENT/ directory." && exit 1)
test -e $ENVIRONMENT/private.tfvars || (echo "No terraform private variables file found at $ENVIRONMENT/private.tfvars" && exit 1)

# Dry run to see if terra.sh can execute without error. This will show any
# errors that might occur if no dist file has been made for instance.
echo "" | ./$ENVIRONMENT/terra.sh console

# Check if terraform variables are setup for a stateful swap deployment.
TEST_is_volatile_active=$(echo "var.is_volatile_active" | \
  ./$ENVIRONMENT/terra.sh console 2> /dev/null | tail -n1)
test "${TEST_is_volatile_active}" = "false" || (echo "
The is_volatile_active terraform variable should be 'false' for a stateful swap deployment.
Try using the './$ENVIRONMENT/terra.sh apply' command if not needing to do
a stateful swap deployment.
" && exit 1)
TEST_old_swap=$(echo "var.old_swap" | \
  ./$ENVIRONMENT/terra.sh console 2> /dev/null | tail -n1 | xargs)
TEST_new_swap=$(echo "var.new_swap" | \
  ./$ENVIRONMENT/terra.sh console 2> /dev/null | tail -n1 | xargs)
TEST_is_swap_a_active=$(echo "var.is_swap_a_active" | \
  ./$ENVIRONMENT/terra.sh console 2> /dev/null | tail -n1)
TEST_is_swap_b_active=$(echo "var.is_swap_b_active" | \
  ./$ENVIRONMENT/terra.sh console 2> /dev/null | tail -n1)
test "${TEST_is_swap_a_active}" = "true" -o "${TEST_is_swap_b_active}" = "true" || (echo "At least one is_swap_a_active or is_swap_b_active terraform variable should be 'true' for a stateful swap deployment." && exit 1)
echo "old_swap = '${TEST_old_swap}'"
echo "new_swap = '${TEST_new_swap}'"

# Determine the old swap and new swap.
if [ "$STEP_STATE" = "1" ]; then
  NEW_SWAP=$(test "$TEST_is_swap_a_active" = "false" -a "$TEST_is_swap_b_active" = "true" && echo "A" || (test "$TEST_is_swap_a_active" = "true" -a "$TEST_is_swap_b_active" = "false" && echo "B" || (echo "Both swaps are inactive or both are active. Only one should be active when on step 1.")))
else
  if [ -e $ENVIRONMENT/.new_swap ]; then
    NEW_SWAP=$(cat $ENVIRONMENT/.new_swap)
  else
    read -p "Unable to determine which will be the new swap. Is it A or B? " NEW_SWAP
    # Uppercase the response.
    NEW_SWAP="${NEW_SWAP^}"
    test "$NEW_SWAP" = "A" -o "$NEW_SWAP" = "B" || (echo "Invalid response. Must enter 'A' or 'B'." && exit 1)
    echo "$NEW_SWAP" > $ENVIRONMENT/.new_swap
  fi
fi
OLD_SWAP=$(test "$NEW_SWAP" = "A" && echo "B" || echo "A")
echo "
old swap is: $OLD_SWAP
new swap is: $NEW_SWAP
"
if [ "$OLD_SWAP" != "$TEST_old_swap" -o "$NEW_SWAP" != "$TEST_new_swap" ]; then
  echo "
ERROR: The old_swap and new_swap values are not consistent with
       is_swap_a_active and is_swap_b_active variables.

Update these variables in the _infra/$ENVIRONMENT/private.tfvars file.
Should be set like this:
old_swap = \"$OLD_SWAP\"
new_swap = \"$NEW_SWAP\"
"
  exit 1
fi

# Check to see if the terraform variables can be modified via setting TF_VAR_*
# environment variables.
TERRAFORM_VARIABLE_NOT_MODIFIABLE_MESSAGE='
The $0 script relies on being able to temporarily set some terraform environment
variables.  These variables should not be set in your .tfvars files as they
would not be able to be overridden by the TF_VAR_* environment variable that this
script temporarily changes.
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


# Default to Step 1. Allow skipping to a step if it is passed as an arg. Check if
# a previous in-progress deployment exists and skip to that step after confirmation.
if [ $STEP_STATE = '1' -a -e $ENVIRONMENT/.deployment_step_state ]; then
  PREVIOUS_STEP=$(cat $ENVIRONMENT/.deployment_step_state)
  read -p "Found previous in-progress deployment state. Do you want to skip to step '$PREVIOUS_STEP'? [y/n]
  " CONFIRM
  if [ "$CONFIRM" = "y" ]; then
    STEP_STATE=$PREVIOUS_STEP
  fi
fi
if [ $STEP_STATE != '1' ]; then
  echo "Skipping to step '$STEP_STATE'."
fi

CURRENT_DNS_TTL=$(dig +nocmd @ns1.digitalocean.com $FQDN +noall +answer | cut -f2)

wait_until_dns_ttl_timeout () {
  echo "Waiting $1 seconds for DNS TTL to timeout."
  sleep $1
  # 64 is the max number of hops a linux system will typically have before it drops the packet.
  echo "Waiting another 64 more seconds to ensure DNS has been fully propagated."
  sleep 64
}

set_step_state () {
  STEP_STATE="$1"
  if [ "$STEP_STATE" = "1" ]; then
    rm -f $ENVIRONMENT/.deployment_step_state
    rm -f $ENVIRONMENT/.new_swap
  elif [ "$STEP_STATE" = "2" ]; then
    echo "$NEW_SWAP" > $ENVIRONMENT/.new_swap
  else
    echo "$STEP_STATE" > $ENVIRONMENT/.deployment_step_state
  fi
}

rollback () {
  echo "Initiating a rollback to old swap $OLD_SWAP"
  read -p "
Update these variables in the _infra/$ENVIRONMENT/private.tfvars file.
Should be set like this:
is_swap_a_active = $(test "$OLD_SWAP" = "A" && echo "true" || echo "false")
is_swap_b_active = $(test "$OLD_SWAP" = "B" && echo "true" || echo "false")
Continue? [y/n] " -n1 CONFIRM
  if [ $CONFIRM != "y" ]; then
    echo "Cancelled rollback."
    exit 0
  fi

  echo "
Updating to the active swap. Also wait for DNS TTL to timeout just in case
floating IP wasn't active."
  ROLLBACK_DNS_TTL=$(dig +nocmd @ns1.digitalocean.com $FQDN +noall +answer | cut -f2)
  TF_VAR_use_short_dns_ttl=true \
  TF_VAR_create_floating_ip_puzzle_massive=true \
  TF_VAR_is_floating_ip_active=true \
    ./$ENVIRONMENT/terra.sh apply
  wait_until_dns_ttl_timeout $ROLLBACK_DNS_TTL

  echo "Updating DNS to point directly to the active swap."
  TF_VAR_use_short_dns_ttl=true \
  TF_VAR_create_floating_ip_puzzle_massive=true \
  TF_VAR_is_floating_ip_active=false \
    ./$ENVIRONMENT/terra.sh apply
  wait_until_dns_ttl_timeout $SHORTER_DNS_TTL

  echo "Remove DO floating IP since it is no longer active."
  TF_VAR_use_short_dns_ttl=true \
  TF_VAR_create_floating_ip_puzzle_massive=false \
    ./$ENVIRONMENT/terra.sh apply

  read -p "
Update these variables in the _infra/$ENVIRONMENT/private.tfvars file.
Should be set like this:
create_legacy_puzzle_massive_swap_a = $(test "$OLD_SWAP" = "A" && echo "true" || echo "false")
create_legacy_puzzle_massive_swap_b = $(test "$OLD_SWAP" = "B" && echo "true" || echo "false")
Continue? [y/n] " -n1 CONFIRM
  if [ $CONFIRM != "y" ]; then
    echo "Cancelled rollback."
    exit 0
  fi

  echo"
Set it back to a longer DNS TTL and remove the new swap that is no longer
active."
  ./$ENVIRONMENT/terra.sh apply

  # Reset to step '1'.
  set_step_state 1
  echo "Rollback complete."
}

step_1 () {
test "$STEP_STATE" != "1" && return
echo "
################################################################################
# 1. Update DNS TTL to be shorter.
################################################################################
"

TF_VAR_use_short_dns_ttl=true \
  ./$ENVIRONMENT/terra.sh apply

echo "Waiting for new shorter DNS TTL to be set."
COUNT=1
while [ $COUNT -le 10 ]; do
  if [ $(dig +nocmd @ns1.digitalocean.com $FQDN +noall +answer | cut -f2) -ne $SHORTER_DNS_TTL ]; then
    COUNT=$(($COUNT+1));
    sleep 10
    printf "."
  else
    break
  fi
done

set_step_state 2
}


step_2 () {
test "$STEP_STATE" != "2" && return
echo "
################################################################################
# 2. Wait until after DNS propagates (depending on previous TTL value).
################################################################################
"

wait_until_dns_ttl_timeout $CURRENT_DNS_TTL

set_step_state 3
}


step_3 () {
test "$STEP_STATE" != "3" && return
echo "
################################################################################
# 3. Add DO floating IP and point to the legacy puzzle massive droplet swap_a
#    or swap_b that is active.
################################################################################
"

TF_VAR_use_short_dns_ttl=true \
TF_VAR_create_floating_ip_puzzle_massive=true \
TF_VAR_is_floating_ip_active=true \
  ./$ENVIRONMENT/terra.sh apply

set_step_state 4
}


step_4 () {
test "$STEP_STATE" != "4" && return
echo "
################################################################################
# 4. Wait until after DNS propagates (depending on shorter TTL value).
################################################################################
"

wait_until_dns_ttl_timeout $SHORTER_DNS_TTL

set_step_state 5
}

step_5 () {
test "$STEP_STATE" != "5" && return
echo "
################################################################################
# 5. Create the new swap for legacy puzzle massive droplet and verify.
################################################################################

Create both swaps here. Only the active swap will be getting traffic since the
floating ip will be pointing to it.
"

read -p "
Update these variables in the _infra/$ENVIRONMENT/private.tfvars file.
Should be set like this:
create_legacy_puzzle_massive_swap_a = true
create_legacy_puzzle_massive_swap_b = true
Continue? [y/n] " -n1 CONFIRM
if [ $CONFIRM != "y" ]; then
  echo "Canceled deployment."
  exit 0
fi

TF_VAR_use_short_dns_ttl=true \
TF_VAR_create_floating_ip_puzzle_massive=true \
TF_VAR_is_floating_ip_active=true \
  ./$ENVIRONMENT/terra.sh apply

echo "Waiting for 80 seconds before attempting to connect to newly provisioned droplet."
# Wait for a bit before trying to connect to the newly provisioned droplet.
sleep 80

# Run Ansible playbooks to setup newly provisioned swap with data from old swap.
# TODO: how to not ask for the become password each time?
ansible-playbook ansible-playbooks/add-host-to-known_hosts.yml \
  -i $ENVIRONMENT/host_inventory.ansible.cfg --limit legacy_puzzle_massive_new_swap

ansible-playbook ansible-playbooks/finished-cloud-init.yml \
  -u dev \
  -i $ENVIRONMENT/host_inventory.ansible.cfg \
  --limit legacy_puzzle_massive_new_swap

# Strange way of getting IP address of new swap.
NEW_SWAP_IP=$(ansible -m debug \
  -i $ENVIRONMENT/host_inventory.ansible.cfg \
  -a "gather_facts=true" \
  -a "var=hostvars[inventory_hostname]" \
  legacy_puzzle_massive_new_swap \
  | sed 's#.*SUCCESS =>##' \
  | jq -r '.["hostvars[inventory_hostname]"].inventory_hostname')

echo "ssh in as dev and set the password if it has been marked to be reset.
ssh dev@${NEW_SWAP_IP}
"
ssh dev@${NEW_SWAP_IP}

test $PROVISION_CERTS -eq 1 \
  && ansible-playbook ansible-playbooks/copy-certs-to-new-swap.yml \
  --ask-become-pass \
  -i $ENVIRONMENT/host_inventory.ansible.cfg \
  || echo 'no copy certs'

ansible-playbook ansible-playbooks/make-install-and-reload-nginx.yml \
  --ask-become-pass \
  -i $ENVIRONMENT/host_inventory.ansible.cfg \
  --limit legacy_puzzle_massive_new_swap

RESOURCES_DIRECTORY=$ENVIRONMENT/resources
RESOURCES_DIRECTORY=$(realpath $RESOURCES_DIRECTORY)
HTPASSWD_FILE=$(realpath $ENVIRONMENT/.htpasswd)
OLD_SWAP_DB_BACKUP=$(realpath $ENVIRONMENT/db-old_swap.dump.gz)
ansible-playbook ansible-playbooks/switch-data-over-to-new-swap.yml \
  --ask-become-pass \
  -i $ENVIRONMENT/host_inventory.ansible.cfg \
  --extra-vars "htpasswd_file=$HTPASSWD_FILE
  old_swap_db_backup=$OLD_SWAP_DB_BACKUP
  resources_directory=$RESOURCES_DIRECTORY"

ansible-playbook ansible-playbooks/appctl-start.yml \
  --ask-become-pass \
  -i $ENVIRONMENT/host_inventory.ansible.cfg --limit legacy_puzzle_massive_new_swap

test $PROVISION_CERTS -eq 1 \
  && ansible-playbook ansible-playbooks/provision-certbot.yml \
  -i $ENVIRONMENT/host_inventory.ansible.cfg --limit legacy_puzzle_massive_new_swap \
  --ask-become-pass \
  --extra-vars "makeenvironment=$(test $ENVIRONMENT = 'development' && echo 'development' || echo 'production')
  testcert=$(test $ENVIRONMENT = 'production' && echo '' || echo '--test-cert')"
  || echo 'no provision certs'

echo "The IP for the new swap '$NEW_SWAP' in $ENVIRONMENT environment is:
$NEW_SWAP_IP
It is recommended to temporarily update your /etc/hosts file to use this ip like so:

# Swap '$NEW_SWAP'
$NEW_SWAP_IP $FQDN

"

read -p "Verify that new swap '$NEW_SWAP' is working correctly. [y/n] " -n1 CONFIRM
if [ $CONFIRM != "y" ]; then
  echo "Cancelled deployment. Old swap '$OLD_SWAP' is currently stopped still."
  read -p "
Rollback to old swap '$OLD_SWAP' now? Another attempt will need to wait until
after the longer DNS TTL when doing a rollback.
Rollback? [y/n] " -n1 CONFIRM
  if [ $CONFIRM != "y" ]; then
    rollback
  else
    exit 0
  fi
fi

read -p "
Update these variables in the _infra/$ENVIRONMENT/private.tfvars file.
Should be set like this:
is_swap_a_active = $(test "$NEW_SWAP" = "A" && echo "true" || echo "false")
is_swap_b_active = $(test "$NEW_SWAP" = "B" && echo "true" || echo "false")
Continue? [y/n] " -n1 CONFIRM
if [ $CONFIRM != "y" ]; then
  echo "Cancelled deployment. Old swap '$OLD_SWAP' is currently stopped still."
  read -p "
Rollback to old swap '$OLD_SWAP' now? Another attempt will need to wait until
after the longer DNS TTL when doing a rollback.
Rollback? [y/n] " -n1 CONFIRM
  if [ $CONFIRM != "y" ]; then
    rollback
  else
    exit 0
  fi
fi

set_step_state 6
}

step_6 () {
test "$STEP_STATE" != "6" && return
echo "
################################################################################
# 6. Update floating IP to point to new swap.
################################################################################
"

TF_VAR_use_short_dns_ttl=true \
TF_VAR_create_floating_ip_puzzle_massive=true \
TF_VAR_is_floating_ip_active=true \
  ./$ENVIRONMENT/terra.sh apply

read -p "New swap '$NEW_SWAP' is now active. Continue with cleaning up old swap '$OLD_SWAP'? [y/n] " -n1 CONFIRM
if [ $CONFIRM != "y" ]; then
  echo "Cancelled deployment. Old swap '$OLD_SWAP' is currently stopped and not active."
  read -p "
 Rollback to old swap '$OLD_SWAP' and make it active now? Another deployment
 attempt will need to wait until after the longer DNS TTL when doing a rollback.

################################################################################
Warning! The new swap '$NEW_SWAP' is active and rolling back to old swap '$OLD_SWAP'
will cause a potential loss of data.
################################################################################

Rollback? [y/n] " -n1 CONFIRM
  if [ $CONFIRM != "y" ]; then
    rollback
  else
    exit 0
  fi
fi

set_step_state 7
}

step_7 () {
test "$STEP_STATE" != "7" && return
echo "
################################################################################
# 7. Remove old swap if everything is looking good.
################################################################################
"

read -p "
Update these variables in the _infra/$ENVIRONMENT/private.tfvars file.
Should be set like this:
create_legacy_puzzle_massive_swap_a = $(test "$NEW_SWAP" = "A" && echo "true" || echo "false")
create_legacy_puzzle_massive_swap_b = $(test "$NEW_SWAP" = "B" && echo "true" || echo "false")
Continue? [y/n] " -n1 CONFIRM
if [ $CONFIRM != "y" ]; then
  echo "Cancelled deployment. Old swap '$OLD_SWAP' is currently stopped and not active."
  exit 0
fi

TF_VAR_use_short_dns_ttl=true \
TF_VAR_create_floating_ip_puzzle_massive=true \
TF_VAR_is_floating_ip_active=true \
  ./$ENVIRONMENT/terra.sh apply

set_step_state 8
}

step_8 () {
test "$STEP_STATE" != "8" && return
echo "
################################################################################
# 8. Update DNS to point to new swap instead of floating IP.
################################################################################
"

TF_VAR_use_short_dns_ttl=true \
TF_VAR_create_floating_ip_puzzle_massive=true \
TF_VAR_is_floating_ip_active=false \
  ./$ENVIRONMENT/terra.sh apply

set_step_state 9
}

step_9 () {
test "$STEP_STATE" != "9" && return
echo "
################################################################################
# 9. Wait until after DNS propagates (depending on previous TTL value).
################################################################################
"

wait_until_dns_ttl_timeout $SHORTER_DNS_TTL

set_step_state 10
}

step_10 () {
test "$STEP_STATE" != "10" && return
echo "
################################################################################
# 10. Remove DO floating IP.
################################################################################
"

TF_VAR_use_short_dns_ttl=true \
TF_VAR_create_floating_ip_puzzle_massive=false \
  ./$ENVIRONMENT/terra.sh apply

set_step_state 11
}

step_11 () {
test "$STEP_STATE" != "11" && return
echo "
################################################################################
# 11. Update DNS TTL to be the longer value that was originally used.
################################################################################
"

./$ENVIRONMENT/terra.sh apply

set_step_state 12
}

step_12 () {
test "$STEP_STATE" != "12" && return
echo "
################################################################################
# 12. Update old_swap and new_swap variables.
################################################################################
"

read -p "
Update these variables in the _infra/$ENVIRONMENT/private.tfvars file.
Should be set like this:
old_swap = \"$NEW_SWAP\"
new_swap = \"$OLD_SWAP\"
Continue? [y/n] " -n1 CONFIRM
  if [ $CONFIRM != "y" ]; then
    echo "Cancelled."
    exit 0
  fi
set_step_state 13
}

step_last () {
test "$STEP_STATE" != "13" && return
echo "
################################################################################
# All done.
################################################################################
"

# Reset to step '1'.
set_step_state 1
}


step_1
step_2
step_3
step_4
step_5
step_6
step_7
step_8
step_9
step_10
step_11
step_12
step_last
