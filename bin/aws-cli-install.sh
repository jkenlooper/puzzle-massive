#!/usr/bin/env bash
set -eu -o pipefail

set -x

# Modified instructions based from
# https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html

# https://github.com/aws/aws-cli/blob/v2/CHANGELOG.rst
# Use output of `md5sum awscliv2.zip` to update the md5sum if bumping the version
AWS_CLI_VERSION=2.2.11
AWSCLIV2_CHECKSUM="a0fdfd071a62f7ad5510cfa606a937b3  awscliv2.zip"

TMPDIR=$(mktemp -d)
cd $TMPDIR
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-${AWS_CLI_VERSION}.zip" -o "awscliv2.zip"
echo "$AWSCLIV2_CHECKSUM" | md5sum --check
unzip awscliv2.zip
./aws/install
