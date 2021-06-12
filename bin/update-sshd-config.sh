#!/usr/bin/env bash

set -euo pipefail

# Disable root SSH login with password
sed --in-place 's/^PermitRootLogin.*/PermitRootLogin prohibit-password/g' /etc/ssh/sshd_config
# Disable password authentication for ssh and only use public keys
sed --in-place 's/^PasswordAuthentication yes$/PasswordAuthentication no/' /etc/ssh/sshd_config
sed --in-place 's/^#PasswordAuthentication yes$/PasswordAuthentication no/' /etc/ssh/sshd_config
if sshd -t -q; then
  systemctl restart sshd
fi
