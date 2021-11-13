SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
project_dir := $(dir $(mkfile_path))

DOCKER := docker

# For debugging what is set in variables
inspect.%:
	@echo $($*)

# Always run.  Useful when target is like targetname.% .
# Use $* to get the stem
FORCE:

objects := package-lock.json .dist

.PHONY: all
all: $(objects)

package-lock.json: package.json Dockerfile
	$(DOCKER) build -f $(project_dir)Dockerfile \
		--target build \
		-t puzzle-massive-client-side-public \
		$(project_dir)
	$(DOCKER) run \
		--name puzzle-massive-client-side-public \
		puzzle-massive-client-side-public \
		npm install --ignore-scripts
	$(DOCKER) cp \
		puzzle-massive-client-side-public:/build/package-lock.json \
		$@
	$(DOCKER) rm \
		puzzle-massive-client-side-public

.dist: package-lock.json
	$(DOCKER) build -f $(project_dir)Dockerfile \
		--target build \
		-t puzzle-massive-client-side-public \
		$(project_dir)
	rm -rf dist
	$(DOCKER) run \
		--name puzzle-massive-client-side-public \
		puzzle-massive-client-side-public \
		npm run build
	$(DOCKER) cp \
		puzzle-massive-client-side-public:/build/dist \
		./
	touch $@




