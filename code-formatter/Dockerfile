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

WORKDIR /home/code_formatter

COPY --chown=code_formatter:code_formatter package.json ./
RUN <<NPM_INSTALL
set -o errexit
node --version
npm --version
chown -R code_formatter:code_formatter /home/code_formatter
su code_formatter -c 'npm install --ignore-scripts'
NPM_INSTALL

COPY --chown=code_formatter:code_formatter .editorconfig ./
COPY --chown=code_formatter:code_formatter .flake8 ./
COPY --chown=code_formatter:code_formatter .prettierrc ./
COPY --chown=code_formatter:code_formatter .eslintrc.json ./
COPY --chown=code_formatter:code_formatter .stylelintrc.json ./

COPY --chown=code_formatter:code_formatter .modified-files.tar ./

RUN <<FORMAT
set -o errexit
su code_formatter -c 'mkdir -p /home/code_formatter/code'
su code_formatter -c 'tar x -f /home/code_formatter/.modified-files.tar \
  -C /home/code_formatter/code'

su code_formatter -c 'npx eslint --fix \
  --no-error-on-unmatched-pattern --exit-on-fatal-error \
  --output-file eslint_errors.log --format unix \
  code || printf "ERROR with eslint"'
touch eslint_errors.log
sed -i 's^/home/code_formatter/code/^^' eslint_errors.log

su code_formatter -c 'npx stylelint --fix --formatter unix "code/**/*.css" > stylelint_errors.log || printf ""'

su code_formatter -c 'npx prettier --write code || printf ""'

su code_formatter -c '/usr/local/src/code-formatter/bin/black code || printf ""'

FORMAT

USER code_formatter

FROM scratch as formatted-files
COPY --from=build /usr/local/src/code-formatter/requirements.txt /code-formatter/requirements.txt
COPY --from=build /home/code_formatter/package-lock.json /code-formatter/package-lock.json
COPY --from=build /home/code_formatter/eslint_errors.log /
COPY --from=build /home/code_formatter/stylelint_errors.log /

COPY --from=build /home/code_formatter/code/ /
