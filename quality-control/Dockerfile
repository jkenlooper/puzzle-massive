# syntax=docker/dockerfile:1.4.1

# TODO This file was generated from the quality-control directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.

# UPKEEP due: "2022-10-08" label: "Alpine Linux base image" interval: "+3 months"
# docker pull alpine:3.16.0
# docker image ls --digests alpine
FROM alpine:3.16.0@sha256:686d8c9dfa6f3ccfc8230bc3178d23f84eeaf7e457f36f271ab1acc53015037c as build


WORKDIR /usr/local/src/quality-control
RUN <<BUILD_DEPENDENCIES
# Install black, nodejs, and npm
set -o errexit
apk update
apk add --no-cache \
  gcc \
  python3 \
  python3-dev \
  libffi-dev \
  build-base \
  coreutils \
  findutils \
  musl-dev
ln -s /usr/bin/python3 /usr/bin/python

addgroup -g 10044 qc
adduser -u 10044 -G qc -s /bin/sh -D qc
chown -R qc:qc /usr/local/src/quality-control

su qc -c 'python -m venv /usr/local/src/quality-control'
su qc -c '/usr/local/src/quality-control/bin/pip install --upgrade pip wheel'

# UPKEEP due: "2022-10-08" label: "black - The Uncompromising Code Formatter" interval: "+3 months"
su qc -c '/usr/local/src/quality-control/bin/pip install --disable-pip-version-check --compile black==22.6.0'

# Create a requirements.txt so the python package versions that were installed
# can be picked up by vulnerability scans easier.
su qc -c '/usr/local/src/quality-control/bin/pip freeze > /usr/local/src/quality-control/requirements.txt'

# Use whatever nodejs version that is available for this Alpine Linux version.
apk add --no-cache nodejs npm

# Don't need these packages after installing black.
apk --purge del \
  gcc \
  python3-dev \
  libffi-dev \
  build-base \
  musl-dev
BUILD_DEPENDENCIES

WORKDIR /home/qc

RUN <<NPM_INSTALL
# Install eslint, prettier, stylelint tools with npm.
set -o errexit
node --version
npm --version

# UPKEEP due: "2022-10-08" label: "eslint, prettier, stylelint" interval: "+3 months"
# Review the included dependencies with static analysis tools.
# Check each one listed on https://socket.dev/
# https://socket.dev/npm/package/eslint/overview/8.20.0
# https://socket.dev/npm/package/eslint-config-prettier/overview/8.5.0
# https://socket.dev/npm/package/prettier/overview/2.7.1
# https://socket.dev/npm/package/stylelint/overview/14.9.1
# https://socket.dev/npm/package/stylelint-config-standard/overview/26.0.0
# https://socket.dev/npm/package/stylelint-config-prettier/overview/9.0.3
cat <<HERE > package.json
{
  "dependencies": {
    "eslint": "8.20.0",
    "eslint-config-prettier": "8.5.0",
    "prettier": "2.7.1",
    "stylelint": "14.9.1",
    "stylelint-config-standard": "26.0.0",
    "stylelint-config-prettier": "9.0.3"
  }
}
HERE

# Use the specified versions set in the package.json, but opt to update the
# package-lock.json with the actual full list of dependencies. The
# package-lock.json can be committed to source control to further help with
# static analysis tools as needed.
chown -R qc:qc /home/qc
su qc -c 'npm install --ignore-scripts'
NPM_INSTALL

COPY --chown=qc:qc .editorconfig ./
COPY --chown=qc:qc .flake8 ./
COPY --chown=qc:qc .prettierrc ./
COPY --chown=qc:qc .eslintrc.json ./
COPY --chown=qc:qc .stylelintrc.json ./

COPY --chown=qc:qc .modified-files.tar ./

RUN <<FORMAT
# Run prettier and black on modified files.
set -o errexit
su qc -c 'mkdir -p /home/qc/code'
su qc -c 'tar x -f /home/qc/.modified-files.tar \
  -C /home/qc/code'
chown -R qc:qc code

su qc -c 'npx prettier --write code'

su qc -c '/usr/local/src/quality-control/bin/black code'

FORMAT

ARG LINT_AUTO_FIX=no
RUN <<LINT
# Run linting tools on formatted code and create error log files.
set -o errexit
if [ "$LINT_AUTO_FIX" = "yes" ]; then
  set -- "--fix"
else
  set --
fi
su qc -c 'npx eslint \
  "$@" \
  --no-error-on-unmatched-pattern --exit-on-fatal-error \
  --output-file eslint_errors.log --format unix \
  code || printf "eslint errors"'
touch eslint_errors.log
sed -i 's^/home/qc/code/^^' eslint_errors.log

if [ "$LINT_AUTO_FIX" = "yes" ]; then
  set -- "--fix"
else
  set --
fi
su qc -c 'npx stylelint "$@" --formatter unix "code/**/*.css" > stylelint_errors.log || printf ""'
touch stylelint_errors.log
sed -i 's^/home/qc/code/^^' stylelint_errors.log

LINT

USER qc

# Only care about the files from the build stage that were made.
FROM scratch as output-files

# Include these for further analysis.
COPY --from=build /usr/local/src/quality-control/requirements.txt /quality-control/requirements.txt
COPY --from=build /home/qc/package-lock.json /quality-control/package-lock.json

# The log files are useful to know which files have errors or other suggested fixes.
COPY --from=build /home/qc/eslint_errors.log /
COPY --from=build /home/qc/stylelint_errors.log /

# Include all the files that were updated so the user has the option to
# overwrite as needed.
COPY --from=build /home/qc/code/ /
