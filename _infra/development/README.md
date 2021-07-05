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

The `_infra/development/legacy_puzzle_massive_droplet-user_data.sh` script
should be uploaded and executed if this is an initial deployment of the
environment. It is used to fully provision the droplet.

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
