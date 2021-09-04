#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

vagrant destroy --force --parallel --no-tty
vagrant up --no-tty --parallel

vagrant provision old_swap --provision-with copy-certs-to-new-swap --no-tty
