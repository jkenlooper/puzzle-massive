#!/usr/bin/env sh

set -o errexit

# This file was generated from the code-formatter directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.

npm run prettier -- --write .
/usr/local/src/code-formatter/bin/black .
