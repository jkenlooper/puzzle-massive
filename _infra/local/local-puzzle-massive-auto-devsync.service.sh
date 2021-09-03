#!/usr/bin/env bash
set -eu -o pipefail

# Allow setting a different user other then the one that is executing the script
user=${1-$(whoami)}

# project directory is two up from this script's directory (_infra/local/)
PROJECT_DIRECTORY=$(realpath $0 | xargs dirname | xargs -I {} realpath {}/../../)

DATE=$(date)

cat <<HERE

# File generated from $0
# on ${DATE}
#
# https://www.freedesktop.org/software/systemd/man/systemd.service.html

[Unit]
Description=Auto devsync local environment
After=multi-user.target

[Service]
Type=exec
User=vagrant
Group=vagrant
WorkingDirectory=$PROJECT_DIRECTORY
Restart=always
ExecStart=$PROJECT_DIRECTORY/bin/distwatch.js

[Install]
WantedBy=multi-user.target

HERE
