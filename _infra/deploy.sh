#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

set -x


ENVIRONMENT=$1
SHORTER_DNS_TTL=300
LONGER_DNS_TTL=3600

wait_until_dns_ttl_timeout () {
  echo "Waiting $1 seconds for DNS TTL to timeout."
  sleep $1
  # 64 is the max number of hops a linux system will typically have before it drops the packet.
  echo "Waiting another 64 more seconds to ensure DNS has been fully propagated."
  sleep 64
}

# Set a local variable for the Fully Qualified Domain Name to what has been set
# for the Terraform variables 'sub_domain' and 'domain' for this environment. The
# ENVIRONMENT variable should be a valid environment like 'development', 'test',
# 'acceptance', or 'production'.

FQDN=$(echo 'format("${var.sub_domain}${var.domain}")' | \
  ./$ENVIRONMENT/terra.sh console 2> /dev/null | tail -n1 | xargs)
echo "The FQDN for the $ENVIRONMENT environment is $FQDN."


# Get the current DNS TTL.

CURRENT_DNS_TTL=$(dig +nocmd @ns1.digitalocean.com $FQDN +noall +answer | cut -f2)
echo "Current DNS TTL is $CURRENT_DNS_TTL seconds for $FQDN."

# 1. Update DNS TTL to be shorter
read -p "Update DNS TTL to be shorter value in seconds (minimum is 30):
" -i $SHORTER_DNS_TTL SHORTER_DNS_TTL

TF_VAR_volatile_dns_ttl=$SHORTER_DNS_TTL
export TF_VAR_volatile_dns_ttl
TF_VAR_dns_ttl=$SHORTER_DNS_TTL
export TF_VAR_dns_ttl
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
TF_VAR_is_floating_ip_active=true ./$ENVIRONMENT/terra.sh apply


# 4. Wait until after DNS propagates (depending on shorter TTL value)
wait_until_dns_ttl_timeout $SHORTER_DNS_TTL

# 5. Create the new swap for legacy puzzle massive droplet and verify
# Create both swaps here. Only the active swap will be getting traffic since the floating ip will be pointing to it.
TF_VAR_create_legacy_puzzle_massive_swap_a=true TF_VAR_create_legacy_puzzle_massive_swap_b=true ./$ENVIRONMENT/terra.sh apply

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
TF_VAR_is_floating_ip_active=false ./$ENVIRONMENT/terra.sh apply

# 9. Wait until after DNS propagates (depending on previous TTL value)
wait_until_dns_ttl_timeout $SHORTER_DNS_TTL

# 10. Remove DO floating IP
# TODO: Might be safer to do this last?
TF_VAR_create_floating_ip_puzzle_massive=false ./$ENVIRONMENT/terra.sh apply


# 11. Update DNS TTL to be longer
TF_VAR_volatile_dns_ttl=$LONGER_DNS_TTL
export TF_VAR_volatile_dns_ttl
TF_VAR_dns_ttl=$LONGER_DNS_TTL
export TF_VAR_dns_ttl
./$ENVIRONMENT/terra.sh apply
