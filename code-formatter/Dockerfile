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

COPY --chown=code_formatter:code_formatter code-formatter/package.json ./
RUN <<NPM_INSTALL
set -o errexit
node --version
npm --version
npm install --ignore-scripts
NPM_INSTALL

COPY --chown=code_formatter:code_formatter code-formatter/format.sh ./
COPY --chown=code_formatter:code_formatter .editorconfig ./
COPY --chown=code_formatter:code_formatter .flake8 ./
COPY --chown=code_formatter:code_formatter .prettierrc ./
COPY --chown=code_formatter:code_formatter .stylelintrc ./

COPY --chown=code_formatter:code_formatter design-tokens/src ./design-tokens/src
COPY --chown=code_formatter:code_formatter mockups ./mockups
COPY --chown=code_formatter:code_formatter source-media ./source-media
COPY --chown=code_formatter:code_formatter root ./root
COPY --chown=code_formatter:code_formatter enforcer ./enforcer
COPY --chown=code_formatter:code_formatter queries ./queries
COPY --chown=code_formatter:code_formatter stream ./stream
COPY --chown=code_formatter:code_formatter client-side-public/src ./client-side-public/src
COPY --chown=code_formatter:code_formatter docs ./docs
COPY --chown=code_formatter:code_formatter api ./api
COPY --chown=code_formatter:code_formatter chill ./chill
COPY --chown=code_formatter:code_formatter chill-data ./chill-data
COPY --chown=code_formatter:code_formatter divulger ./divulger
COPY --chown=code_formatter:code_formatter documents ./documents
COPY --chown=code_formatter:code_formatter templates ./templates
RUN <<FORMAT
set -o errexit
mkdir -p /home/code_formatter/code/.last-modified
chown -R code_formatter:code_formatter /home/code_formatter/code/.last-modified
su code_formatter -c 'npm run format'
FORMAT

USER code_formatter

FROM scratch as formatted-files
COPY --from=build /usr/local/src/code-formatter/requirements.txt /code-formatter/requirements.txt
COPY --from=build /home/code_formatter/code/package-lock.json /code-formatter/package-lock.json

COPY --from=build /home/code_formatter/code/design-tokens/src /design-tokens/src
COPY --from=build /home/code_formatter/code/mockups /mockups
COPY --from=build /home/code_formatter/code/source-media /source-media
COPY --from=build /home/code_formatter/code/root /root
COPY --from=build /home/code_formatter/code/enforcer /enforcer
COPY --from=build /home/code_formatter/code/queries /queries
COPY --from=build /home/code_formatter/code/stream /stream
COPY --from=build /home/code_formatter/code/client-side-public/src /client-side-public/src
COPY --from=build /home/code_formatter/code/docs /docs
COPY --from=build /home/code_formatter/code/api /api
COPY --from=build /home/code_formatter/code/chill /chill
COPY --from=build /home/code_formatter/code/chill-data /chill-data
COPY --from=build /home/code_formatter/code/divulger /divulger
COPY --from=build /home/code_formatter/code/documents /documents
COPY --from=build /home/code_formatter/code/templates /templates
