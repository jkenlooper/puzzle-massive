# Reformats any code that is newer than the last time it formatted code
#
# Run this makefile from the top level of the project:
# make format -f ./code-formatter/code-formatter.mk

# TODO This file was generated from the code-formatter directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.

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

objects := $(project_dir).formatted-files.tar

.PHONY: all
all: $(objects)

$(project_dir).modified-files.tar: $(shell find design-tokens/src/ -type f -print) $(shell find mockups/ -type f -print) $(shell find source-media/ -type f -print) $(shell find root/ -type f -print) $(shell find enforcer/ -type f -print) $(shell find queries/ -type f -print) $(shell find stream/ -type f -print) $(shell find client-side-public/src/ -type f -print) $(shell find docs/ -type f -print) $(shell find api/ -type f -print) $(shell find chill/ -type f -print) $(shell find chill-data/ -type f -print) $(shell find divulger/ -type f -print) $(shell find documents/ -type f -print) $(shell find templates/ -type f -print)
	$(project_dir)modified-files-manifest.sh

# Copy these into the code formatter project directory so the docker build
# context can use them.
$(project_dir).editorconfig: .editorconfig
	cp $^ $@

$(project_dir).flake8: .flake8
	cp $^ $@

$(project_dir).prettierrc: .prettierrc
	cp $^ $@

$(project_dir).eslintrc.json: .eslintrc.json
	cp $^ $@

$(project_dir).stylelintrc.json: .stylelintrc.json
	cp $^ $@

$(project_dir).formatted-files.tar: $(project_dir)package.json $(project_dir)Dockerfile $(project_dir).modified-files.tar $(project_dir).editorconfig $(project_dir).flake8 $(project_dir).prettierrc $(project_dir).eslintrc.json $(project_dir).stylelintrc.json
	rm -f $@
	$(DOCKER) image rm puzzlemassive-code-formatter-files || printf ""
	DOCKER_BUILDKIT=1 $(DOCKER) build -f $(project_dir)Dockerfile \
									--progress=plain \
		--target formatted-files \
		-t puzzlemassive-code-formatter-files \
		--output type=tar,dest=$@ \
		$(project_dir)
	# TODO overwrite files with new formatted ones
	#-tar x -f $@ --overwrite
	-tar t -f $@
	touch $@


