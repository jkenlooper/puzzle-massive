# Reformats any code that is newer than files in
# ./code-formatter/.last-modified/*
#
# Run this makefile from the top level of the project:
# make format -f ./code-formatter/code-formatter.mk

# This file was generated from the code-formatter directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.

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
		-t puzzlemassive-code-formatter \
		./
	$(DOCKER) run \
		--name puzzlemassive-code-formatter \
		puzzlemassive-code-formatter \
		npm install --ignore-scripts
	$(DOCKER) cp \
		puzzlemassive-code-formatter:/code/package-lock.json \
		$@
	$(DOCKER) rm \
		puzzlemassive-code-formatter

.PHONY: format
format: $(project_dir)package-lock.json
	$(DOCKER) build -f code-formatter.dockerfile \
		-t puzzlemassive-code-formatter \
		./
	$(DOCKER) run -it --rm \
		--mount type=bind,src=$(PWD)/code-formatter/.last-modified,dst=/code/.last-modified \
		--mount type=bind,src=$(PWD)/design-tokens/src,dst=/code/design-tokens/src \
		--mount type=bind,src=$(PWD)/mockups,dst=/code/mockups \
		--mount type=bind,src=$(PWD)/source-media,dst=/code/source-media \
		--mount type=bind,src=$(PWD)/root,dst=/code/root \
		--mount type=bind,src=$(PWD)/enforcer,dst=/code/enforcer \
		--mount type=bind,src=$(PWD)/queries,dst=/code/queries \
		--mount type=bind,src=$(PWD)/stream,dst=/code/stream \
		--mount type=bind,src=$(PWD)/client-side-public/src,dst=/code/client-side-public/src \
		--mount type=bind,src=$(PWD)/docs,dst=/code/docs \
		--mount type=bind,src=$(PWD)/api,dst=/code/api \
		--mount type=bind,src=$(PWD)/chill,dst=/code/chill \
		--mount type=bind,src=$(PWD)/chill-data,dst=/code/chill-data \
		--mount type=bind,src=$(PWD)/divulger,dst=/code/divulger \
		--mount type=bind,src=$(PWD)/documents,dst=/code/documents \
		--mount type=bind,src=$(PWD)/templates,dst=/code/templates \
		puzzlemassive-code-formatter \
		npm run format




