#!/usr/bin/env bash

set -euo pipefail

# Create dev user and immediately expire password to force a change on login
useradd --create-home --shell "/bin/bash" --user-group --groups sudo dev
passwd --delete dev
chage --lastday 0 dev

# Create SSH directory for sudo user and move keys over
home_directory="$(eval echo ~dev)"
mkdir --parents "${home_directory}/.ssh"
cp /root/.ssh/authorized_keys "${home_directory}/.ssh"
chmod 0700 "${home_directory}/.ssh"
chmod 0600 "${home_directory}/.ssh/authorized_keys"
chown --recursive dev:dev "${home_directory}/.ssh"
