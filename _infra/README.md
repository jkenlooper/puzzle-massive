# Puzzle Massive Infrastructure as Code

[Terraform](https://www.terraform.io/) is used to automate creating the
different environments that are deployed outside of the local machine. The
Development, Test, Acceptance, and Production environments
([DTAP](https://en.wikipedia.org/wiki/Development,_testing,_acceptance_and_production))
are deployed with a supported
[IaaS provider](https://registry.terraform.io/browse/providers?category=infrastructure&tier=official%2Cpartner).
At this time, [DigitalOcean](https://m.do.co/c/686c08019031) is the preferred
IaaS provider.

[Vagrant](https://www.vagrantup.com/) is used to develop the code on
the **local** machine. It is useful to create a local instance
of Puzzle Massive that can be modified and tweaked. Or use it as your own
personal Puzzle Massive site that only is accessible from your machine.

Many of the steps to install and get everything working for this is done with
some scripts that handle automating these things. Shell scripts written in Bash,
Python, and Node.js are used to do all the _cool ninja stuff_ and most are in
the `bin/` directory.

## Environments

The environments are largely based off of the different git branches. Follow the
[GitFlow Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
for the git branching model that are used for these environments. This is
recommended if you plan to make a change and submit a Pull Request in GitHub for
the project.

### Local Environment

**Git branch: `feature/*`, `bugfix/*`**

It is recommended to use the Vagrant setup instructions in the [development
guide](/docs/development.md). Other ways of creating virtual machines with
virtualization software can be used as long as they use Ubuntu 20.04. Can also
directly install Puzzle Massive on your machine without using a virtual machine
if you use Ubuntu 20.04.

Setting up a local environment may involve some troubleshooting. Please ask for
help on the Discord Chat development channel.

When developing a feature or fixing a bug; use the branch naming convention of
prefixing it with 'feature/' or 'bugfix/'. For example, if working on a feature
to add rotating pieces; then use the branch name of 'feature/rotating-pieces'.
For fixing a bug with pieces that mysteriously disappear then use
'bugfix/bad-kitty'.

Please create an issue, or comment on an existing issue, if you are actively
working on it. I (Jake Hickenlooper) will then assign the issue to you so others
know who is working on what. Please also comment if you are no longer actively
working on that issue so others might pick up where you left off.

Create a pull request when the feature or bugfix is ready. The pull request
should target the `develop` git branch on the GitHub
[jkenlooper/puzzle-massive](https://github.com/jkenlooper/puzzle-massive)
repository.

[Vagrant Share](https://www.vagrantup.com/docs/share) can be used to expose the
local instance remotely if using Vagrant on the local machine. I have no
experience with this and it is untested.

### Development Environment

**Git branch: `develop`**

The `develop` git branch is the branch that any new features or bug fixes should
be based from.

Deployed initially with Terraform and then updated and provisioned as needed.
The `_infra/development/legacy_puzzle_massive_droplet-user_data.sh` script that
is created should be used to fully provision the droplet.

_Development instances are secured with a firewall that **blocks all inbound
requests to ports 80 and 443**._ Ports 80 and 443 are the web server ports for
HTTP and HTTPS. These are blocked because debug mode is usually enabled on the
development instance and is a security risk if open to the public.

### Test Environment

**Git tag: `test/*`**

_Work in Progress_

Short-lived environment that is based from a tagged commit. The created
instance also uses a firewall that blocks inbound requests to the web server for
ports 80 and 443. The commit that is tagged
should be from the development branch, but could really be any branch. The
naming convention for test tags should be descriptive. If this test is for an
upcoming release then name it with the next version
(test/release-2.2.2-alpha.1). Otherwise, use the name of the feature or bugfix.

_Git tags with test/ as their prefix may be removed later to clean things up._

- Debug mode is off by default since load testing may be used and the site should be
  configured much like the production site.

- [Cypress](https://www.cypress.io/) for doing integration tests will be used.

- Unit tests for both client side code (Javascript) and server side code (Python)
  will be used.

- Manual testing can also be done here since not every scenario is covered by
  automated tests.

- Load testing and simulate puzzle activity with the puzzle-massive-testdata script.

### Acceptance Environment

**Git branch: `release`, `hotfix/*`**

_Work in Progress_

Create a temporary instance for staging the release. This uses a recent backup copy of
the production data, but is **not** used for production deployments. The instance
is destroyed after it passes acceptance.

A `hotfix/*` branch should be created off of the `production` branch when
needing to quickly patch something that is on production. This should only be
done if the issue is causing an impact to users on the live site. The normal
process to go through the test environment is skipped and only an acceptance
environment is created from the hotfix branch.

### Production Environment

**Git branch: `production`**

_Work in Progress_

Either a new instance is created when following stateful swap deployments or it is
updated in-place.

A git tag of the version is created after successfully deploying to production.

---

## Terraform Usage and Guide

[Terraform](https://www.terraform.io/) is used to automate deploying the
different environments as needed. You do not need to install the `terraform`
cli, or get a DigitalOcean account, if you only plan to work on the Puzzle
Massive site locally on your own machine.

The setup here is designed for small scale and **no shared state** between
individuals deploying updates. This is only meant to be used by a single
developer that will be doing all deployments from their local machine. It will
be up to that developer to maintain proper backups of the terraform state files
that are generated.

Environments are mapped to Terraform Workspaces and also have their own
directory here. Each environment has it's own `config.tfvars` var file.

[DigitalOcean](https://m.do.co/c/686c08019031) is used as the IaaS Provider. An
account with DigitalOcean is required in order to get an access token. Access
token should be kept private and never checked into source control (git) for
obvious reasons. It is not my fault if you leaked one of your access tokens.
Please promptly delete it from your DigitalOcean account if you suspect it has
been compromised.

## Setup

Create a `_infra/puzzle-massive.auto.tfvars` file by copying the example one at
`_infra/example.tfvars` and filling in the variables.

Install terraform and initialize if haven't done so.

```bash
terraform init
```

A helper script for each environment can be used when running the terraform
commands in a workspace. See the README.md for each environment.

- [Development](/_infra/development/README.md)
- [Test](/_infra/test/README.md)
- [Acceptance](/_infra/acceptance/README.md)
- [Production](/_infra/production/README.md)

### Stateful Swap Production Deployment

The stateful swap deployment involves creating a new swap server with the new
distribution and then removing the old swap server. This process has many steps
involved because the application is stateful (SQLite database, Redis, and puzzle
resource files).

An overview of the steps involved are shown below:

1. Update DNS TTL to be shorter
2. Wait until after DNS propagates (depending on previous TTL value)
3. Add DO floating IP and point to the legacy puzzle massive droplet swap_a or swap_b that is active
4. Wait until after DNS propagates (depending on shorter TTL value)
5. Create the new swap for legacy puzzle massive droplet and verify
6. Update floating IP to point to new swap
7. Remove old swap if everything is looking good
8. Update DNS to point to new swap instead of floating IP
9. Wait until after DNS propagates (depending on previous TTL value)
10. Remove DO floating IP
11. Update DNS TTL to be longer
12. Update old_swap and new_swap variables

These steps can be done via the stateful swap deploy script and involve running
various commands including Terraform and Ansible commands. The script is
interactive and will also allow starting at a specific step if necessary.

```bash
./bin/stateful_swap_deploy.sh $ENVIRONMENT
```

### In-Place Production Deployment

The in-place deployment requires fewer steps than the stateful swap deployment.
This deployment can be used when the changes are minor. It will update the
application in-place instead of creating a whole new server to swap over to.

It is recommended to test an in-place deployment by running it against the
acceptance environment that was stood up with the same version that is in
production. See /\_infra/acceptance/README.md

Set the ENVIRONMENT variable as needed for doing an in-place
deployment. The dist file will need to be created by running the `make dist`
command on the development machine.

```bash
./bin/in-place-quick-deploy.sh $ENVIRONMENT
```

TODO: Create a rollback Ansible playbook for a failed in-place deployment.

---

## Ansible Usage and Guide

Install any Ansible requirements like collections and roles.

```bash
ansible-galaxy install -r ansible-requirements.yml
```

### Maintenance Tasks

These Ansible playbooks should be run from the `_infra/` directory and set the ENVIRONMENT variable
as needed.

```bash
# Example of setting and exporting ENVIRONMENT variable
ENVIRONMENT=development
export ENVIRONMENT
```

#### Update Packages and Reboot

This will run an apt-get update and reboot the machine.

```bash
./bin/update-packages-and-reboot.sh $ENVIRONMENT
```

#### Add Admin User

Access to the admin only section is protected via basic auth as well as only
allowing certain IP addresses access to the admin only section of the site.

Include the IP address that will be allowed for accessing the admin only section
by adding it the Terraform variable admin_ips. The local file at
`_infra/$ENVIRONMENT/allow_deny_admin.nginx.conf` is generated from the
admin_ips variable. This Ansible playbook will upload that file and reload the
NGINX service.

1. Add an admin user with a password to be able to access the admin only section

   ```bash
   ./bin/add-user-to-basic-auth.sh $ENVIRONMENT
   ```

2. Include the IP address that will be allowed access to the Terraform variable 'admin_ips' (usually set in `private.auto.tfvars`)

3. Apply the changes using Terraform command in order to update the local `allow_deny_admin.nginx.conf` file and firewall

   ```bash
   ./$ENVIRONMENT/terra.sh apply
   ```

4. Upload the new file and reload NGINX

   ```bash
   ./bin/update-allow_deny_admin_nginx_conf.sh $ENVIRONMENT
   ```

#### Manage Puzzle Resources and Database

Stop the app and it will create a backup database dump file which will be
uploaded to the S3 bucket.

```bash
./bin/appctl-stop.sh $ENVIRONMENT
```

Start the app and it's services.

```bash
./bin/appctl-start.sh $ENVIRONMENT
```

Stop the app and it's services and also run make, make install. Useful if only
updated the .env file or something. The app should start at the end of the make
install.

```bash
./bin/appctl-stop-and-make-install-and-reload-nginx.sh $ENVIRONMENT
```

Download the puzzle resources directory _to_ the local machine.

```bash
./bin/sync-legacy-puzzle-massive-resources-directory-to-local.sh $ENVIRONMENT
```

Replace the database with a local database dump file.

```bash
./bin/restore-db-on-legacy-puzzle-massive.sh $ENVIRONMENT
```

Upload the puzzle resources directory _from_ the local machine.

```bash
./bin/sync-legacy-puzzle-massive-resources-directory-from-local.sh $ENVIRONMENT
```

### Ad-hoc Command

```bash
ENVIRONMENT=development

ansible \
 legacy_puzzle_massive \
 -i $ENVIRONMENT/host_inventory.ansible.cfg \
 -m command \
 -a "echo 'hi'"
```
