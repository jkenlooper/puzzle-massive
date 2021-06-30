# Script is inlined as part of cloud-init user_data
# #!/usr/bin/env bash
# set -eu -o pipefail
# set -x

# Set when uploaded to droplet
# ARTIFACT
# .env file created from heredoc ENV_CONTENT
# .htpasswd file created from heredoc HTPASSWD_CONTENT
# aws_config file created from heredoc AWS_CONFIG
# aws_credentials file created from heredoc AWS_CREDENTIALS
# EPHEMERAL_DIR created from _infra/one-time-bucket-object-grab.tmpl

pwd_dir=$PWD
TMPDIR=$(mktemp -d)
cp .env $TMPDIR/
cp .htpasswd $TMPDIR/
(cd $TMPDIR

  mkdir bin
  mv $EPHEMERAL_DIR/*.sh bin/
  chmod +x bin/*.sh

  # Execute scripts as needed for this environment
  ./bin/add-dev-user.sh
  ./bin/update-sshd-config.sh
  ./bin/set-external-puzzle-massive-in-hosts.sh
  ./bin/setup.sh
  ./bin/iptables-setup-firewall.sh

  mkdir -p /home/dev/.aws
  mv $pwd_dir/aws_config /home/dev/.aws/config
  chmod 0600 /home/dev/.aws/config
  mv $pwd_dir/aws_credentials /home/dev/.aws/credentials
  chmod 0600 /home/dev/.aws/credentials

  mv $EPHEMERAL_DIR/$ARTIFACT /home/dev/

  # At this time both the development environment and test environment use the
  # same infra-development-build.sh script.
  ./bin/infra-development-build.sh $ARTIFACT $(realpath .env) $(realpath .htpasswd)
)
