FROM node:16-buster

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

VOLUME /code/api
VOLUME /code/client-side-public/src
VOLUME /code/design-tokens/src
VOLUME /code/divulger
VOLUME /code/docs
VOLUME /code/documents
VOLUME /code/enforcer
VOLUME /code/mockups
VOLUME /code/queries
VOLUME /code/root
VOLUME /code/stream
VOLUME /code/templates

CMD ["npm", "run"]
