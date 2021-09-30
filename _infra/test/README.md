# Test Environment and Terraform Workspace

The test environment should be a short lived project that is deployed in order
to run the full suite of unit tests, integration tests, and allow for any manual
testing. A git tag with the prefix 'test/' is created in order to allow testing
from any git commit.

```bash
# Create a tag for the test environment
git tag test/2.3.4
```

Use the helper script for running the normal terraform commands. These should
be ran from the `_infra/` directory since that is where the `.tf` files are
located.

This requires setting the tfvars in order to create resources on DigitalOcean.
The command `source secure_tfvars.sh` will prompt for the required access keys.
Alternately, the command to encrypt these access keys to disk can be used:
`source encrypt_tfvars.sh test`. They can then be decrypted and set via
the command `source decrypt_tfvars.sh test`.

```bash
# Show the terraform plan
./test/terra.sh plan

# Apply the plan after confirmation
./test/terra.sh apply
```

## Check on the Droplet Setup

It will take a few minutes for the cloudinit to finish running the
`_infra/test/legacy_puzzle_massive_droplet-user_data.sh` script. The output log
for it can be tailed:

```bash
# On the droplet server
tail -f /var/log/cloud-init-output.log
```

Example of setting and exporting ENVIRONMENT variable

```bash
ENVIRONMENT=test
export ENVIRONMENT
```

Check on the progress of a newly initialized legacy puzzle massive droplet.

```bash
./bin/finished-cloud-init.sh $ENVIRONMENT
```

## Clean Up

After all the testing is done the project can be destroyed.

```bash
# Destroy the project after confirmation
./test/terra.sh destroy
```
