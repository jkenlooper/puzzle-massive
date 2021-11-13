# Puzzle Massive Client Side Public

This directory contains the JavaScript, CSS, and other source files that will be
used by web browsers when displaying the main Puzzle Massive public site.


## Building

If not actively working on these source files, then execute the `make` command
to create the necessary files in the dist/ directory.

```bash
# In the client-side-public directory.
make
```

## Developing

Use the docker commands when actively making changes to the source files. These
will watch the source files for changes and rebuild the files in the dist/
directory.

```bash
docker build \
  --target build \
  -t puzzle-massive-client-side-public \
  ./

# TODO: configure the site to use base URL in order to get these directly from
# host instead of through NGINX server in the virtual machine?
docker run -it --rm \
  -p 0.0.0.0:38688:38688 \
  --mount type=bind,src=$(pwd)/src,dst=/build/src \
  --name puzzle-massive-client-side-public \
  puzzle-massive-client-side-public \
  npm run watch
```


## Serving

```bash
# In the client-side-public/ directory.
docker build \
  -t puzzle-massive-client-side-public \
  ./

docker run -it --rm \
  -p 0.0.0.0:38688:38688 \
  --name puzzle-massive-client-side-public \
  puzzle-massive-client-side-public
```
