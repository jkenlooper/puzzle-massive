# This file in the parent directory design-tokens was generated from the design-tokens directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.
# Version: 0.0.2-alpha.1

SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
project_dir := $(dir $(mkfile_path))
slugname := puzzlemassive

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
	DOCKER_BUILDKIT=1 $(DOCKER) build --progress=plain -f $(project_dir)Dockerfile \
		--target build \
		-t $(slugname)-design-tokens-build \
		$(project_dir)
	$(DOCKER) run \
		--name $(slugname)-design-tokens-build \
		$(slugname)-design-tokens-build \
		npm install --ignore-scripts
	$(DOCKER) cp \
		$(slugname)-design-tokens-build:/build/package-lock.json \
		$@
	$(DOCKER) rm \
		$(slugname)-design-tokens-build

.dist: package-lock.json postcss.config.js custom-properties-selector.cjs $(shell find src/ -type f)
	rm -rf dist
	DOCKER_BUILDKIT=1 $(DOCKER) build --progress=plain -f $(project_dir)Dockerfile \
		--target build \
		-t $(slugname)-design-tokens-build \
		$(project_dir)
	$(DOCKER) run \
		--name $(slugname)-design-tokens-build \
		$(slugname)-design-tokens-build \
		ls -alR /build/dist/
	$(DOCKER) cp \
		$(slugname)-design-tokens-build:/build/dist \
		$(project_dir)
	$(DOCKER) rm \
		$(slugname)-design-tokens-build
	touch $(@)
