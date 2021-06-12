#!/usr/bin/env bash

set -euo pipefail

# Set the external-puzzle-massive for internal use. Which makes much sense.
echo "127.0.0.1 external-puzzle-massive" >> /etc/hosts
