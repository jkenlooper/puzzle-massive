# Development Environment and Terraform Workspace

The development environment is used to show changes that have been merged to the
develop branch.

Use the helper script for running the normal terraform commands. These should
be ran from the `_infra/` directory since that is where the `.tf` files are
located.

```bash
# Initialize with a SQLite database file to use when first creating droplet.
# Starting with a copy of an existing db.dump.gz is optional.
cp path-to-your-own/db.dump.gz development/db.dump.gz
```

```bash
# Source the secure_tfvars.sh script if haven't set TF_VAR_* variables yet.
source secure_tfvars.sh

# Show the terraform plan
./development/terra.sh plan

# Apply the plan after confirmation
./development/terra.sh apply
```

## Add Data From Local

Sync a local resources directory to the development environment. The directories
in the resources directory might be empty if the site is configured to use the
s3 bucket to store puzzle image files.

```bash
read -p "Enter the path to puzzle massive resources directory:
" RESOURCES_DIRECTORY
ENVIRONMENT=development \
 ansible-playbook ansible-playbooks/sync-legacy-puzzle-massive-resources-directory.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 --extra-vars "
 resources_directory=$RESOURCES_DIRECTORY
 "
```

A db.dump.gz file can also replace an existing database for the development
environment. A common use case for doing this would be to match what is
currently in production by downloading a backup db.dump.gz file. Note that when
first creating the development environment the `_infra/development/db.dump.gz`
is used.

```bash
read -p "Enter the path to a db.dump.gz to replace the current sqlite database
with:
" DB_DUMP_FILE
ENVIRONMENT=development \
 ansible-playbook ansible-playbooks/restore-db-on-legacy-puzzle-massive.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 --extra-vars "
 db_dump_file=$DB_DUMP_FILE
 "
```

## Accessing the Droplet

This development environment has a firewall that blocks all IP addresses from
hitting the web server by default except localhost. It is expected to use `ssh`
to set up a proxy with the server in order to access it with a web browser.

A SOCKS proxy can be configured on your local machine in order to view.
Assuming that there is an entry for local-puzzle-massive that points to your
digitalocean droplet in /etc/hosts file.

```bash
# ssh to the droplet and bind the 7171 port
ssh -D 7171 dev@THE_IP_OF_THE_DROPLET
```

Then setup your SOCKS v5 host to be localhost and 7171 port
Recommended to use FireFox web browser to set SOCKS proxy instead of changing
your whole system.

## Clean Up

Destroy the development environment when it is no longer needed.

```bash
# Destroy the project when it is no longer needed
./development/terra.sh destroy
```
