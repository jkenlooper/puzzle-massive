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

objects := $(project_dir)formatted-files.tar

.PHONY: all
all: $(objects)

$(project_dir)formatted-files.tar: $(project_dir)package.json $(project_dir)Dockerfile $(wildcard design-tokens/src/*) $(wildcard mockups/*) $(wildcard source-media/*) $(wildcard root/*) $(wildcard enforcer/*) $(wildcard queries/*) $(wildcard stream/*) $(wildcard client-side-public/src/*) $(wildcard docs/*) $(wildcard api/*) $(wildcard chill/*) $(wildcard chill-data/*) $(wildcard divulger/*) $(wildcard documents/*) $(wildcard templates/*)
	$(DOCKER) image rm puzzlemassive-code-formatter-files || printf ""
	DOCKER_BUILDKIT=1 $(DOCKER) build -f $(project_dir)Dockerfile \
		--target formatted-files \
		-t puzzlemassive-code-formatter-files \
		--output type=tar,dest=$(project_dir)formatted-files.tar \
		.
	-tar x --overwrite -f $(project_dir)formatted-files.tar
