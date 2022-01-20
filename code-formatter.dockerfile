FROM node:16-buster

# This code-formatter.dockerfile should be at the top-level of the project.

# This file was generated from the code-formatter directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.

RUN apt-get --yes update && apt-get --yes upgrade
RUN apt-get --yes install python3 \
  python3-dev \
  python3-pip \
  software-properties-common \
  gcc
RUN pip3 install black==21.10b0

WORKDIR /code

COPY code-formatter/package.json ./
COPY code-formatter/package-lock.json ./

RUN chown -R node:node /code
USER node

RUN node --version \
    && npm --version \
    && npm ci --ignore-scripts

COPY .editorconfig ./
COPY .flake8 ./
COPY .prettierrc ./
COPY .stylelintrc ./
COPY code-formatter/format.sh ./

VOLUME /code/.last-modified

CMD ["npm", "run"]
