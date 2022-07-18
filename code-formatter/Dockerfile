# syntax=docker/dockerfile:1.4.1

# This code-formatter.dockerfile should be at the top-level of the project.

# This file was generated from the code-formatter directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.

# UPKEEP due: "2022-10-08" label: "Alpine Linux base image" interval: "+3 months"
# docker pull alpine:3.16.0
# docker image ls --digests alpine
FROM alpine:3.16.0@sha256:686d8c9dfa6f3ccfc8230bc3178d23f84eeaf7e457f36f271ab1acc53015037c as build


WORKDIR /usr/local/src/code-formatter
RUN <<BUILD_DEPENDENCIES
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

addgroup -g 10044 code_formatter
adduser -u 10044 -G code_formatter -s /bin/sh -D code_formatter
chown -R code_formatter:code_formatter /usr/local/src/code-formatter

su code_formatter -c 'python -m venv /usr/local/src/code-formatter'
su code_formatter -c '/usr/local/src/code-formatter/bin/pip install --upgrade pip wheel'
su code_formatter -c '/usr/local/src/code-formatter/bin/pip install --disable-pip-version-check --compile black==22.6.0'
# Create a requirements.txt so the python package versions that were installed
# can be picked up by vulnerability scans easier.
su code_formatter -c '/usr/local/src/code-formatter/bin/pip freeze > /usr/local/src/code-formatter/requirements.txt'

apk add --no-cache nodejs npm
apk --purge del \
  gcc \
  python3-dev \
  libffi-dev \
  build-base \
  musl-dev
BUILD_DEPENDENCIES

WORKDIR /home/code_formatter/code

COPY --chown=code_formatter:code_formatter package.json ./
RUN <<NPM_INSTALL
set -o errexit
node --version
npm --version
npm install --ignore-scripts
mv package-lock.json /home/code_formatter/
NPM_INSTALL

COPY --chown=code_formatter:code_formatter format.sh ./

COPY --chown=code_formatter:code_formatter .editorconfig ./
COPY --chown=code_formatter:code_formatter .flake8 ./
COPY --chown=code_formatter:code_formatter .prettierrc ./
COPY --chown=code_formatter:code_formatter .stylelintrc ./

COPY --chown=code_formatter:code_formatter .modified-files.tar /home/code_formatter/.modified-files.tar

RUN <<FORMAT
set -o errexit
tar x -f /home/code_formatter/.modified-files.tar \
  --exclude=node_modules \
  --exclude=package.json \
  --exclude=format.sh
chown -R code_formatter:code_formatter ./

su code_formatter -c 'npm run format'

rm -rf node_modules
mv package.json /home/code_formatter/
rm format.sh
rm -f .editorconfig
rm -f .flake8
rm -f .prettierrc
rm -f .stylelintrc
FORMAT

USER code_formatter

FROM scratch as formatted-files
COPY --from=build /usr/local/src/code-formatter/requirements.txt /code-formatter/requirements.txt
COPY --from=build /home/code_formatter/package-lock.json /code-formatter/package-lock.json

COPY --from=build /home/code_formatter/code/ /
