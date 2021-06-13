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
(cd $TMPDIR

  # Grab necessary scripts from the GitHub Repo
  mkdir bin
  cd bin
  curl --location --silent --remote-name-all \
    "https://raw.githubusercontent.com/jkenlooper/puzzle-massive/${CHECKOUT_COMMIT}/bin/{add-dev-user.sh,update-sshd-config.sh,set-external-puzzle-massive-in-hosts.sh,infra-development-build.sh}"
  cd ..
  md5sum --check checksums

  chmod +x bin/*.sh

  # Execute scripts as needed for this environment
  ./bin/add-dev-user.sh
  ./bin/update-sshd-config.sh
  ./bin/set-external-puzzle-massive-in-hosts.sh

  ./bin/infra-development-build.sh $CHECKOUT_COMMIT $REPOSITORY_CLONE_URL $(realpath .env) $(realpath .htpasswd)

)
