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

This requires setting the tfvars in order to create resources on DigitalOcean.
The command `source secure_tfvars.sh` will prompt for the required access keys.
Alternately, the command to encrypt these access keys to disk can be used:
`source encrypt_tfvars.sh development`. They can then be decrypted and set via
the command `source decrypt_tfvars.sh development`.

```bash
# Show the terraform plan
./development/terra.sh plan

# Apply the plan after confirmation
./development/terra.sh apply
```

It will take a few minutes for the cloudinit to finish running the
`_infra/development/legacy_puzzle_massive_droplet-user_data.sh` script. The output log
for it can be tailed:

```bash
# On the droplet server
tail -f /var/log/cloud-init-output.log
```

Check on the progress of a newly initialized legacy puzzle massive droplet.
Depending on how quickly this playbook is executed; use either the '-u dev' or
'-u root'.

```bash
ENVIRONMENT=development
ansible-playbook ansible-playbooks/finished-cloud-init.yml \
 -u dev \
 -i $ENVIRONMENT/host_inventory.ansible.cfg --limit legacy_puzzle_massive
```

## Add Data From Local

Sync a local resources directory to the development environment. The directories
in the resources directory might be empty if the site is configured to use the
s3 bucket to store puzzle image files.

```bash
read -p "Enter the path to puzzle massive resources directory:
" RESOURCES_DIRECTORY

# Verify that directory exists
RESOURCES_DIRECTORY=$(realpath $RESOURCES_DIRECTORY)
test -d $RESOURCES_DIRECTORY || echo "no directory at $RESOURCES_DIRECTORY"

ENVIRONMENT=development

ansible-playbook ansible-playbooks/sync-legacy-puzzle-massive-resources-directory.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 -u dev \
 --ask-become-pass \
 --extra-vars "resources_directory=$RESOURCES_DIRECTORY"
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

# Verify that file exists
DB_DUMP_FILE=$(realpath $DB_DUMP_FILE)
test -e $DB_DUMP_FILE || echo "no file at $DB_DUMP_FILE"

ENVIRONMENT=development

ansible-playbook ansible-playbooks/restore-db-on-legacy-puzzle-massive.yml \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 -u dev \
 --ask-become-pass \
 --extra-vars "db_dump_file=$DB_DUMP_FILE"
```

## Accessing the Droplet

This development environment has a firewall that blocks all IP addresses from
hitting the web server by default except those listed in the Terraform variables
developer_ips and admin_ips. You'll need to include your IP address in those
variables in order to get access.

## Clean Up

Destroy the development environment when it is no longer needed.

```bash
# Destroy the project when it is no longer needed
./development/terra.sh destroy
```
