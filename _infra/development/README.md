# Development Environment and Terraform Workspace

The development environment is used to show changes that have been merged to the
develop branch.

Use the helper script for running the normal terraform commands. These should
be ran from the `_infra/` directory since that is where the `.tf` files are
located.

```bash
# Show the terraform plan
./development/terra.sh plan

# Apply the plan after confirmation
./development/terra.sh apply
```

```bash
# Destroy the project when it is no longer needed
./development/terra.sh destroy
```

This development environment has a firewall that blocks all IP addresses from
hitting the web server by default except localhost. It is expected to use `ssh`
to set up a proxy with the server in order to access it with a web browser.
