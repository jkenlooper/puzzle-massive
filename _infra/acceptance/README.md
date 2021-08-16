# Acceptance Environment and Terraform Workspace

The acceptance environment is used to verify that everything looks good when
using a recent copy of the production data.

Use the helper script for running the normal terraform commands. These should
be ran from the `_infra/` directory since that is where the `.tf` files are
located.

```bash
# Show the terraform plan
./acceptance/terra.sh plan

# Apply the plan after confirmation
./acceptance/terra.sh apply
```

## Optional Create and Destroy SSL Certificates

The commands to create the SSL Certificates with the Let's Encrypt certbot can
be tested out in the Acceptance environment. This step is optional since the
site can be run with just http scheme. The site also uses a protocol-relative
URL ( '//' instead of 'http://' or 'https://' ) for any URLs that need to be
absolute. Note that the Production environment will always provision certbot and
use SSL certs, but can also be accessed without them.

```bash
# Run the Ansible playbook to provision SSL Certificates
ENVIRONMENT=acceptance \
 ansible-playbook ansible-playbooks/provision-certbot.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 --extra-vars "
 makeenvironment=$(test $ENVIRONMENT = 'development' && echo 'development' || echo 'production')"
```

## Test Out In-Place Production Deployment

This assumes that the version has already been tested in the Development and
Test environments and a dist file for that version exists.

First create a copy of the same version that is currently in production.

```bash
# Checkout previous version that is in production and apply.
git checkout master
./acceptance/terra.sh apply
```

Then test the in-place quick deploy which will upgrade that version to the next
one.

```bash
# Switch back to the 'release' branch
git checkout release

# Run the Ansible playbook for in-place deployments
project_version=$(jq -r '.version' ../package.json)
ENVIRONMENT=acceptance \
DIST_FILE=puzzle-massive-$project_version.tar.gz \
 ansible-playbook ansible-playbooks/in-place-quick-deploy.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 --extra-vars "
 message_file=../$ENVIRONMENT/puzzle-massive-message.html
 dist_file=../../$DIST_FILE
 environment=$(test $ENVIRONMENT = 'development' && echo 'development' || echo 'production')"
```

Verify that the new version works correctly in the Acceptance environment.

## Clean up

First, stop the auto renewal if certbot was provisioned for the Acceptance environment.

```bash
# unregister certbot account
ENVIRONMENT=acceptance \
 ansible-playbook ansible-playbooks/remove-certbot.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg
```

```bash
# Destroy the project when it is no longer needed
./acceptance/terra.sh destroy
```
