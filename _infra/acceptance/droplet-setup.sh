#!/usr/bin/env bash

# Set when uploaded to droplet
# CHECKOUT_COMMIT
# REPOSITORY_CLONE_URL
# .env file created from heredoc ENV_CONTENT
# .htpasswd file created from heredoc HTPASSWD_CONTENT
# checksums file created from heredoc BIN_CHECKSUMS
# aws_config file created from heredoc AWS_CONFIG
# aws_credentials file created from heredoc AWS_CREDENTIALS

set -euo pipefail

TMPDIR=$(mktemp -d)
mv .env $TMPDIR/
mv .htpasswd $TMPDIR/
mv checksums $TMPDIR/
(cd $TMPDIR

  # Grab necessary scripts from the GitHub Repo
  mkdir bin
  cd bin
  curl --location --silent --remote-name-all \
    "https://raw.githubusercontent.com/jkenlooper/puzzle-massive/${CHECKOUT_COMMIT}/bin/{add-dev-user.sh,update-sshd-config.sh,set-external-puzzle-massive-in-hosts.sh,setup.sh,iptables-setup-firewall.sh,infra-development-build.sh}"
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

  mkdir /home/dev/.aws
  mv $pwd_dir/aws_config /home/dev/.aws/config
  chmod 0600 /home/dev/.aws/config
  mv $pwd_dir/aws_credentials /home/dev/.aws/credentials
  chmod 0600 /home/dev/.aws/credentials

  ./bin/infra-acceptance-build.sh $CHECKOUT_COMMIT $REPOSITORY_CLONE_URL $(realpath .env) $(realpath .htpasswd)
)
