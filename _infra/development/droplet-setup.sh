#!/usr/bin/env bash

# Set when uploaded to droplet
# CHECKOUT_COMMIT
# REPOSITORY_CLONE_URL
# .env file created from heredoc ENV_CONTENT
# .htpasswd file created from heredoc HTPASSWD_CONTENT
# checksums file created from heredoc BIN_CHECKSUMS

set -euo pipefail

TMPDIR=$(mktemp -d)
cp .env $TMPDIR/
cp .htpasswd $TMPDIR/
cp checksums $TMPDIR/
(cd $TMPDIR

  # Grab necessary scripts from the GitHub Repo
  mkdir bin
  cd bin
  curl --location --silent --remote-name-all \
    "https://raw.githubusercontent.com/jkenlooper/puzzle-massive/${CHECKOUT_COMMIT}/bin/{add-dev-user.sh,update-sshd-config.sh,set-external-puzzle-massive-in-hosts.sh,setup.sh,iptables-setup-firewall.sh,aws-cli-install.sh,infra-development-build.sh}"
  cd ..
  md5sum --check checksums

  chmod +x bin/*.sh

  # Execute scripts as needed for this environment
  ./bin/add-dev-user.sh
  ./bin/update-sshd-config.sh
  ./bin/set-external-puzzle-massive-in-hosts.sh
  ./bin/setup.sh
  ./bin/iptables-setup-firewall.sh
  ./bin/aws-cli-install.sh

  # At this time both the development environment and test environment use the
  # same infra-development-build.sh script.
  ./bin/infra-development-build.sh $CHECKOUT_COMMIT $REPOSITORY_CLONE_URL $(realpath .env) $(realpath .htpasswd)
)
