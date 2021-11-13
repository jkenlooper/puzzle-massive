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

objects := package-lock.json dist/v1/default.css

.PHONY: all
all: $(objects)

package-lock.json: package.json Dockerfile
	$(DOCKER) build -f $(project_dir)Dockerfile \
		--target build \
		-t puzzle-massive-design-tokens-build \
		$(project_dir)

	$(DOCKER) run \
		--name puzzle-massive-design-tokens-build \
		puzzle-massive-design-tokens-build \
		npm install --ignore-scripts

	$(DOCKER) cp \
		puzzle-massive-design-tokens-build:/build/package-lock.json \
		$@

	$(DOCKER) rm \
		puzzle-massive-design-tokens-build

# For backward compatibility with legacy_puzzle_massive; copy the built CSS file
dist/v1/default.css: package-lock.json custom-properties-selector.cjs $(shell find src/ -type f)
	$(DOCKER) build -f $(project_dir)Dockerfile \
		--target build \
		-t puzzle-massive-design-tokens-build \
		$(project_dir)

	mkdir -p $$(dirname $(project_dir)$(@))

	$(DOCKER) run \
		--name puzzle-massive-design-tokens-build \
		puzzle-massive-design-tokens-build \
		ls -alR /build/dist/

	$(DOCKER) cp \
		puzzle-massive-design-tokens-build:/build/$(@) \
		$(project_dir)$(@)

	$(DOCKER) rm \
		puzzle-massive-design-tokens-build
