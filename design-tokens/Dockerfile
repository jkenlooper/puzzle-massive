FROM node:16-alpine as build

# Include git command in case a dependency in package.json refers to a git
# repository.
# The theo package is no longer maintained and no new version has been pushed.
# The package.json is set to get theo directly from github.
RUN apk add git

# Create an unprivileged user that will only have access to /build directory.
RUN addgroup -g 2000 puzzlemassive \
    && adduser -u 2000 -G puzzlemassive -s /bin/sh -D puzzlemassive

WORKDIR /build

COPY . ./

RUN chown -R puzzlemassive:puzzlemassive /build

RUN ls -al

USER puzzlemassive
RUN node --version \
    && npm --version \
    && npm ci --ignore-scripts

RUN npm run build || echo "Failed build"

CMD ["npm"]

### Serve
# TODO: this will eventually be used instead of just copying the built files.

FROM lipanski/docker-static-website:1.0.0

COPY --from=build /build/dist /home/static

# Need a Cache-Control:max-age=0 header (thttpd option '-M 0') on all responses.
CMD ["/thttpd", "-D", "-h", "0.0.0.0", "-p", "38687", "-d", "/home/static", "-u", "static", "-l", "-", "-M", "0"]
