#!/usr/bin/env bash
set -eu -o pipefail

RUN_COMMAND=$1

[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm

# Use the node and npm that is set in .nvmrc
nvm use;

npm run "$RUN_COMMAND";
