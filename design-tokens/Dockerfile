# syntax=docker/dockerfile:1.3.0-labs

# This file in the parent directory design-tokens was generated from the design-tokens directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.
# Version: 0.0.1

FROM node:16-alpine as build

# Include git command in case a dependency in package.json refers to a git
# repository.
# The theo package is no longer maintained and no new version has been pushed.
# The package.json is set to get theo directly from github.
WORKDIR /build

COPY package.json ./
COPY package-lock.json ./
RUN <<INSTALL
# Create an unprivileged user that will only have access to /build directory.
addgroup -g 2000 dev
adduser -u 2000 -G dev -s /bin/sh -D dev
chown -R dev:dev /build
apk update
apk add --no-cache \
  git
# Use the unprivileged user when using npm install
su dev -c 'npm ci --ignore-scripts'
# Cleanup
apk --purge del \
  git
INSTALL

RUN <<FILEWATCH_SUPPORT
apk update
apk add --no-cache \
  entr

mkdir -p .tmp
chown -R dev:dev .tmp
cat <<'MEOW' > dev.sh
#!/usr/bin/env sh
rm -f .tmp/watch_files
for d in src; do
  find ./$d >> .tmp/watch_files
done
cat .tmp/watch_files | entr -rzdn npm run dev
MEOW
chmod +x dev.sh
chown dev:dev dev.sh
FILEWATCH_SUPPORT

USER dev

COPY custom-properties-selector.cjs ./
COPY postcss.config.js ./
COPY src ./src
COPY transform-design-tokens.sh ./

ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}

RUN <<BUILD
npm run build || echo "Failed build"
BUILD

EXPOSE 8080

CMD ["./dev.sh"]

### Serve
FROM lipanski/docker-static-website:1.0.0@sha256:ea8516e6b2928c3c1b1c6737f7e32e03b10a04f978080592e61c3dbe2871ff1a


COPY --from=build /build/dist /home/static

# Need a Cache-Control:max-age=0 header (thttpd option '-M 0') on all responses.
CMD ["/thttpd", "-D", "-h", "0.0.0.0", "-p", "8080", "-d", "/home/static", "-u", "static", "-l", "-", "-M", "0"]
