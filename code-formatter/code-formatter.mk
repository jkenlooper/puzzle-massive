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

objects := $(project_dir)package-lock.json format

.PHONY: all
all: $(objects)

$(project_dir)package-lock.json: $(project_dir)package.json code-formatter.dockerfile
	$(DOCKER) build -f code-formatter.dockerfile \
		-t puzzle-massive-code-formatter \
		./
	$(DOCKER) run \
		--name puzzle-massive-code-formatter \
		puzzle-massive-code-formatter \
		npm install --ignore-scripts
	$(DOCKER) cp \
		puzzle-massive-code-formatter:/code/package-lock.json \
		$@
	$(DOCKER) rm \
		puzzle-massive-code-formatter

.PHONY: format
format: $(project_dir)package-lock.json
	$(DOCKER) build -f code-formatter.dockerfile \
		-t puzzle-massive-code-formatter \
		./
	$(DOCKER) run -it --rm \
		--mount type=bind,src=$(PWD)/code-formatter/.last-modified,dst=/code/.last-modified \
		--mount type=bind,src=$(PWD)/api,dst=/code/api \
		--mount type=bind,src=$(PWD)/client-side-public/src,dst=/code/client-side-public/src \
		--mount type=bind,src=$(PWD)/design-tokens/src,dst=/code/design-tokens/src \
		--mount type=bind,src=$(PWD)/divulger,dst=/code/divulger \
		--mount type=bind,src=$(PWD)/docs,dst=/code/docs \
		--mount type=bind,src=$(PWD)/documents,dst=/code/documents \
		--mount type=bind,src=$(PWD)/enforcer,dst=/code/enforcer \
		--mount type=bind,src=$(PWD)/mockups,dst=/code/mockups \
		--mount type=bind,src=$(PWD)/queries,dst=/code/queries \
		--mount type=bind,src=$(PWD)/root,dst=/code/root \
		--mount type=bind,src=$(PWD)/stream,dst=/code/stream \
		--mount type=bind,src=$(PWD)/templates,dst=/code/templates \
		puzzle-massive-code-formatter \
		npm run format




