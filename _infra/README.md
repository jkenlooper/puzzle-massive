# Puzzle Massive Infrastructure as Code

_This is a bit of a wish-list of best practices and a work in progress of
existing stuff._

[Terraform](https://www.terraform.io/) will be used to automate handling the
different environments as needed.

[Vagrant](https://www.vagrantup.com/) is typically used to develop the code on
the local development machine. It is useful to quickly setup a local instance
of Puzzle Massive ready for a developer to make changes to and closely resembles
a production environment.

Shell scripts written in Bash and Python are used to do all the _cool ninja stuff_.

## Environments

The environments are largely based off of the different git branches. Follow the
[GitFlow Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
for the git branching model that are used for these environments.

## Local Environment

**Git branch: `feature/*`, `bugfix/*`**

It is recommended to use the Vagrant setup instructions in the [development
guide](/docs/development.md). Other ways of creating virtual machines with
virtualization software can be used as long as they use Ubuntu 20.04. Can also
directly install Puzzle Massive on your machine without using a virtual machine
if you use Ubuntu 20.04 which is the current OS that the project is built
around.

Setting up a local environment mostly involves following the [development
guide](/docs/development.md) and troubleshooting any issues as you come across
them. Help is available on the Discord Chat Development channel.

When developing a feature or fixing a bug use the branch naming convention of
prefixing it with 'feature/' or 'bugfix/'. For example, if working on a feature
to add rotating pieces; then use the branch name of 'feature/rotating-pieces'.
For fixing a bug with pieces that mysteriously disappear then use
'bugfix/bad-kitty'.

Please create an issue, or comment on an existing issue, if you are actively
working on it. You may also assign the issue to yourself so others know who is
working on what. Please also comment if you are no longer actively working on
that issue so others might pick up where you left off.

Create a pull request when the feature or bugfix is ready. The pull request
should target the `develop` git branch.

## Development Environment

**Git branch: `develop`**

The `develop` git branch is the branch that any new features or bug fixes should
be based from.

Debug mode can be enabled for this environment.

A process to automatically deploy to this environment when changes occur can be
done by setting up a continuous integration and deployment action.

Each developer can create their own development instance which can be deployed
locally or remotely with a supported
[IaaS provider](https://registry.terraform.io/browse/providers?category=infrastructure&tier=official%2Cpartner). At this time, DigitalOcean is the preferred IaaS provider.

[Vagrant Share](https://www.vagrantup.com/docs/share) can be used to expose the
local instance remotely if using Vagrant on the local machine.

_Development instances should be secured by blocking un-authenticated users since
debug mode is usually enabled for these._

## Test Environment

**Git tag: `test/*`**

Short-lived environment can be created from a tagged commit. The created
instance is only accessible to authorized users. The commit that is tagged
should be from the development branch, but could really be any branch. The
naming convention for test tags should be descriptive. If this test is for an
upcoming release then name it with the next version
(test/release-2.2.2-alpha.1), otherwise use the name of the feature or bugfix.

_Git tags with test/ as their prefix may be removed later to clean things up._

- Debug mode is off.

- [Cypress](https://www.cypress.io/) for doing integration tests will be used.

- Unit tests for both client side code (Javascript) and server side code (Python)
  will be used.

- Manual testing can also be done here since not every scenario is covered by
  automated tests.

- Load testing and simulate puzzle activity with the puzzle-massive-testdata script.

## Acceptance Environment

**Git branch: `release`, `hotfix/*`**

Create a temporary instance for staging the release. This uses a recent copy of
the production data, but is not used for blue/green deployments. The instance
is destroyed after it passes acceptance.

A `hotfix/*` branch should be created off of the `production` branch when
needing to quickly patch something that is on production. This should only be
done if the issue is causing an impact to users on the live site. The normal
process to go through the test environment is skipped and only an acceptance
environment is created from the hotfix branch. This new acceptance environment
does not replace an acceptance environment that may already be active.

## Production Environment

**Git branch: `production`**

Either a new instance is created when following blue/green deployments or it is
updated in-place.

A git tag of the version is created after successfully deploying to production.
