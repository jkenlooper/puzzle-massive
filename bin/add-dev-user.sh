#!/usr/bin/env bash

set -euo pipefail

# Sets the dev user with the initial passphrase and marks it as expired to force
# the dev user to change it as soon as they login.

PASSPHRASE=$1

# gecos option will prevent the other informational prompts
adduser dev --disabled-login --disabled-password --gecos ""
echo "dev:$PASSPHRASE" | chpasswd
usermod -aG sudo dev

# Create SSH directory for sudo user and move keys over
home_directory="$(eval echo ~dev)"
mkdir --parents "${home_directory}/.ssh"
cp /root/.ssh/authorized_keys "${home_directory}/.ssh"
chmod 0700 "${home_directory}/.ssh"
chmod 0600 "${home_directory}/.ssh/authorized_keys"
chown --recursive dev:dev "${home_directory}/.ssh"
