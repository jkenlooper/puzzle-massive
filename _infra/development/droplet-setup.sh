#!/usr/bin/env bash

# Set when uploaded to droplet
#CHECKOUT_COMMIT
#REPOSITORY_CLONE_URL
# .env file created from heredoc ENV_CONTENT
# .htpasswd file created from heredoc HTPASSWD_CONTENT

set -euo pipefail

TMPDIR=$(mktemp -d)
cp .env $TMPDIR/
cp .htpasswd $TMPDIR/
(cd $TMPDIR

  # Update these by running:
  # md5sum bin/{clear_nginx_cache.sh,backup.sh}
  # TODO: settle on scripts that will be used and verified. These are just examples.
  (cat <<-'CHECKSUMS'
  ba327924a7b45c0c0bde1f9326f29a52  bin/clear_nginx_cache.sh
  084867ad45d23418941649b79488940a  bin/backup.sh
CHECKSUMS
  ) > checksums
  # TODO: create checksums in a different way?
  #printf "%s" "$CHECKSUMS_CONTENT" > checksums

  # Grab necessary scripts from the GitHub Repo
  mkdir bin
  cd bin
  curl --location --silent --remote-name-all \
    "https://raw.githubusercontent.com/jkenlooper/puzzle-massive/${CHECKOUT_COMMIT}/bin/{clear_nginx_cache.sh,backup.sh}"
  cd ..
  md5sum --check checksums

  chmod +x bin/*.sh

  # Execute scripts as needed for this environment
  ./bin/add-dev-user.sh
  ./bin/update-sshd-config.sh
  ./bin/set-external-puzzle-massive-in-hosts.sh

  ./bin/infra-development-build.sh $CHECKOUT_COMMIT $REPOSITORY_CLONE_URL $(realpath .env) $(realpath .htpasswd)

)
