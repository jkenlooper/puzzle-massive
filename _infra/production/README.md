# Production Environment and Terraform Workspace

The production environment can be initialized with a copy of a db.dump.gz file.
Place that in SQLite database file at the `_infra/production/db.dump.gz` path
when first provisioning this environment.

Use the helper script for running the normal terraform commands. These should
be ran from the `_infra/` directory since that is where the `.tf` files are
located.

This requires setting the tfvars in order to create resources on DigitalOcean.
The command `source secure_tfvars.sh` will prompt for the required access keys.
Alternately, the command to encrypt these access keys to disk can be used:
`source encrypt_tfvars.sh production`. They can then be decrypted and set via
the command `source decrypt_tfvars.sh production`.

```bash
# Show the terraform plan
./production/terra.sh plan

# Apply the plan after confirmation
./production/terra.sh apply
```

Example of setting and exporting ENVIRONMENT variable

```bash
ENVIRONMENT=production
export ENVIRONMENT
```

Check on the progress of a newly initialized legacy puzzle massive droplet.

```bash
./bin/finished-cloud-init.sh $ENVIRONMENT
```

## Optional Create SSL Certificates

The commands to create the SSL Certificates with the Let's Encrypt certbot can
be used in the Production environment. This step is optional since the
site can be run with just http scheme. The site also uses a protocol-relative
URL ( '//' instead of 'http://' or 'https://' ) for any URLs that need to be
absolute. Note that the Production environment should always provision certbot
and use SSL certs, but can also be accessed without them.

```bash
./bin/provision-certbot.sh $ENVIRONMENT
```

## Synchronize Puzzle Massive Resources Directory

Sync a local resources directory to the production environment. The directories
in the resources directory might be empty if the site is configured to use the
s3 bucket to store puzzle image files.

```bash
./bin/sync-legacy-puzzle-massive-resources-directory-from-local.sh $ENVIRONMENT
```

## In-Place Deployment

This assumes that the version has already been tested in the Development and
Test environments and a dist file for that version exists.

```bash
./bin/in-place-quick-deploy.sh $ENVIRONMENT
```

Verify that the new version works correctly in the Production environment.

## Stateful Swap Deployment

The stateful swap deployment works by creating a new Puzzle Massive instance and
copying all the data over from the current instance before switching traffic
over to it.

```bash
./bin/stateful_swap_deploy.sh $ENVIRONMENT
```

## Clean up

Remove certbot auto renewal process and delete the provisioned certificate for
the domain if the `./bin/provision-certbot.sh` script was used on the Production
environment.

```bash
./bin/remove-certbot.sh $ENVIRONMENT
```

Destroy the project when it is no longer needed. Or update the
/production/private.tfvars to not create any of the droplets and then run the
`./production/terra.sh apply` command.

```bash
./production/terra.sh destroy
```
