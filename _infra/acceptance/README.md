# Acceptance Environment and Terraform Workspace

The acceptance environment is used to verify that everything looks good when
using a recent copy of the production data. A less than 24 hour old db.dump.gz
will need to be added at the `_infra/acceptance/db.dump.gz` path. This should
be taken from the production environment. A recent copy of the Puzzle Massive
resources directory should also be available and can be synchronized after the
acceptance environment is provisioned.

Use the helper script for running the normal terraform commands. These should
be ran from the `_infra/` directory since that is where the `.tf` files are
located.

This requires setting the tfvars in order to create resources on DigitalOcean.
The command `source secure_tfvars.sh` will prompt for the required access keys.
Alternately, the command to encrypt these access keys to disk can be used:
`source encrypt_tfvars.sh acceptance`. They can then be decrypted and set via
the command `source decrypt_tfvars.sh acceptance`.

```bash
# Show the terraform plan
./acceptance/terra.sh plan

# Apply the plan after confirmation
./acceptance/terra.sh apply
```

Example of setting and exporting ENVIRONMENT variable

```bash
ENVIRONMENT=acceptance
export ENVIRONMENT
```

Check on the progress of a newly initialized legacy puzzle massive droplet.

```bash
./bin/finished-cloud-init.sh $ENVIRONMENT
```

## Optional Create SSL Certificates

The commands to create the SSL Certificates with the Let's Encrypt certbot can
be tested out in the Acceptance environment. This step is optional since the
site can be run with just http scheme. The site also uses a protocol-relative
URL ( '//' instead of 'http://' or 'https://' ) for any URLs that need to be
absolute. Note that the Production environment should always provision certbot
and use SSL certs, but can also be accessed without them.

```bash
./bin/provision-certbot.sh $ENVIRONMENT
```

## Synchronize Puzzle Massive Resources Directory

Sync a local resources directory to the acceptance environment. The directories
in the resources directory might be empty if the site is configured to use the
s3 bucket to store puzzle image files.

```bash
./bin/sync-legacy-puzzle-massive-resources-directory-from-local.sh $ENVIRONMENT
```

## Test Out In-Place Deployment

This assumes that the version has already been tested in the Development and
Test environments and a dist file for that version exists.

First create a copy of the same version that is currently in production.

```bash
# Checkout previous version that is in production and apply.
git checkout master
./acceptance/terra.sh apply

# Wait until it's finished and the site is up.
./bin/finished-cloud-init.sh $ENVIRONMENT
```

Then test the in-place quick deploy which will upgrade that version to the next
one.

```bash
# Switch back to the 'release' branch
git checkout release

./bin/in-place-quick-deploy.sh $ENVIRONMENT
```

Verify that the new version works correctly in the Acceptance environment.

## Test Out Stateful Swap Deployment

The stateful swap deployment works by creating a new Puzzle Massive instance and
copying all the data over from the current instance before switching traffic
over to it.

```bash
./bin/stateful_swap_deploy.sh $ENVIRONMENT
```

## Clean up

Remove certbot auto renewal process and delete the provisioned certificate for
the domain if the `./bin/provision-certbot.sh` script was used on the Acceptance
environment.

```bash
./bin/remove-certbot.sh $ENVIRONMENT
```

Destroy the project when it is no longer needed. Or update the
/acceptance/private.tfvars to not create any of the droplets and then run the
`./acceptance/terra.sh apply` command.

```bash
./acceptance/terra.sh destroy
```
