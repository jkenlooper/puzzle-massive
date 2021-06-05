#!/usr/bin/env bash
set -eu -o pipefail

# Allow setting a different user other then the one that is executing the script
user=${1-$(whoami)}

# project directory is two up from this script's directory (_infra/local/)
PROJECT_DIRECTORY=$(realpath $0 | xargs dirname | xargs -I {} realpath {}/../../)
LOCAL_WATCHIT_SCRIPT=$(realpath $0 | xargs dirname | xargs -I {} realpath {}/watchit.sh)

DATE=$(date)

cat <<HERE

# File generated from $0
# on ${DATE}
#
# https://www.freedesktop.org/software/systemd/man/systemd.service.html

[Unit]
Description=Watch project directory
After=multi-user.target

[Service]
Type=exec
User=$user
Group=$user
WorkingDirectory=$PROJECT_DIRECTORY
Restart=on-success
ExecStart=$LOCAL_WATCHIT_SCRIPT $PROJECT_DIRECTORY

[Install]
WantedBy=multi-user.target

HERE
