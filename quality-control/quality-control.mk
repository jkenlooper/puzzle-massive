# Reformats any code that is newer than the last time it formatted code
#
# Run this makefile from the top level of the project:
# make -f ./quality-control/quality-control.mk

# TODO This file was generated from the quality-control directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.

SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
qc_dir := $(dir $(mkfile_path))

DOCKER := docker

# For debugging what is set in variables
inspect.%:
	@echo $($*)

# Always run.  Useful when target is like targetname.% .
# Use $* to get the stem
FORCE:

objects := $(qc_dir).formatted-files.tar $(qc_dir).modified-files.tar $(qc_dir).editorconfig $(qc_dir).flake8 $(qc_dir).eslintrc.json $(qc_dir).stylelintrc.json

.PHONY: all
all: $(objects)

# Copy these into the quality control project directory so the docker build
# context can use them.
$(qc_dir).editorconfig: .editorconfig
	cp $^ $@

$(qc_dir).flake8: .flake8
	cp $^ $@

$(qc_dir).prettierrc: .prettierrc
	cp $^ $@

$(qc_dir).eslintrc.json: .eslintrc.json
	cp $^ $@

$(qc_dir).stylelintrc.json: .stylelintrc.json
	cp $^ $@

$(qc_dir).formatted-files.tar: $(qc_dir)Dockerfile $(qc_dir).modified-files.tar $(qc_dir).editorconfig $(qc_dir).flake8 $(qc_dir).prettierrc $(qc_dir).eslintrc.json $(qc_dir).stylelintrc.json
	@rm -f $@
	@$(DOCKER) image rm puzzlemassive-quality-control-files 2> /dev/null || printf ""
	DOCKER_BUILDKIT=1 $(DOCKER) build -f $(qc_dir)Dockerfile \
		--target output-files \
		-t puzzlemassive-quality-control-files \
		--output type=tar,dest=$@ \
		$(qc_dir)
	@echo ""
	-tar t -f $@
	@echo ""
	@echo "Overwrite files in project directory with the formatted files from $@ file? [y/n]"
	@read -r overwrite_files_confirm && if [ "$$overwrite_files_confirm" = "y" ]; then tar x -f $@ --overwrite; fi
	touch $@

.PHONY: lint-auto-fix
lint-auto-fix: $(qc_dir).lint-fix-files.tar

$(qc_dir).lint-fix-files.tar: $(qc_dir)Dockerfile $(qc_dir).modified-files.tar $(qc_dir).editorconfig $(qc_dir).flake8 $(qc_dir).prettierrc $(qc_dir).eslintrc.json $(qc_dir).stylelintrc.json
	@rm -f $@
	@$(DOCKER) image rm puzzlemassive-quality-control-files 2> /dev/null || printf ""
	DOCKER_BUILDKIT=1 $(DOCKER) build -f $(qc_dir)Dockerfile \
		--build-arg LINT_AUTO_FIX=yes \
		--target output-files \
		-t puzzlemassive-quality-control-files \
		--output type=tar,dest=$@ \
		$(qc_dir)
	@echo ""
	-tar t -f $@
	@echo ""
	@echo "Overwrite files in project directory with the changed files from $@ file? [y/n]"
	@read -r overwrite_files_confirm && if [ "$$overwrite_files_confirm" = "y" ]; then tar x -f $@ --overwrite; fi
	touch $@

.PHONY: clean
clean:
	rm $(objects)
