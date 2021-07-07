#!/usr/bin/env bash

set -euo pipefail

USERNAME=$1
PASSPHRASE=$2

htpasswd_file=/srv/puzzle-massive/.htpasswd
mkdir -p $(dirname $htpasswd_file)
touch $htpasswd_file
chown nginx:nginx $htpasswd_file
chmod 0400 $htpasswd_file
echo "$USERNAME:"$(perl -le "print crypt('$PASSPHRASE', '$(tr -dc A-Za-z0-9_ < /dev/urandom | head -c 26)')") >> $htpasswd_file

echo "Added $USERNAME to the $htpasswd_file and will now attempt to reload nginx."

test "$(systemctl is-active nginx)" = "active" && systemctl reload nginx || echo "The nginx service has not been reloaded since it is not active."
