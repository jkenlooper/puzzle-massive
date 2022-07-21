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
code_formatter_dir := $(dir $(mkfile_path))

DOCKER := docker

# For debugging what is set in variables
inspect.%:
	@echo $($*)

# Always run.  Useful when target is like targetname.% .
# Use $* to get the stem
FORCE:

objects := $(code_formatter_dir).formatted-files.tar $(code_formatter_dir).modified-files.tar $(code_formatter_dir).editorconfig $(code_formatter_dir).flake8 $(code_formatter_dir).eslintrc.json $(code_formatter_dir).stylelintrc.json

.PHONY: all
all: $(objects)

$(code_formatter_dir).modified-files.tar:
	$(code_formatter_dir)modified-files-manifest.sh

# Copy these into the code formatter project directory so the docker build
# context can use them.
$(code_formatter_dir).editorconfig: .editorconfig
	cp $^ $@

$(code_formatter_dir).flake8: .flake8
	cp $^ $@

$(code_formatter_dir).prettierrc: .prettierrc
	cp $^ $@

$(code_formatter_dir).eslintrc.json: .eslintrc.json
	cp $^ $@

$(code_formatter_dir).stylelintrc.json: .stylelintrc.json
	cp $^ $@

$(code_formatter_dir).formatted-files.tar: $(code_formatter_dir)Dockerfile $(code_formatter_dir).modified-files.tar $(code_formatter_dir).editorconfig $(code_formatter_dir).flake8 $(code_formatter_dir).prettierrc $(code_formatter_dir).eslintrc.json $(code_formatter_dir).stylelintrc.json
	@rm -f $@
	@$(DOCKER) image rm puzzlemassive-code-formatter-files 2> /dev/null || printf ""
	DOCKER_BUILDKIT=1 $(DOCKER) build -f $(code_formatter_dir)Dockerfile \
		--target output-files \
		-t puzzlemassive-code-formatter-files \
		--output type=tar,dest=$@ \
		$(code_formatter_dir)
	@echo ""
	-tar t -f $@
	@echo ""
	@echo "Overwrite files in project directory with the formatted files from $@ file? [y/n]"
	@read -r overwrite_files_confirm && if [ "$$overwrite_files_confirm" = "y" ]; then tar x -f $@ --overwrite; fi
	touch $@

.PHONY: lint_auto_fix
lint_auto_fix: $(code_formatter_dir).lint-fix-files.tar

$(code_formatter_dir).lint-fix-files.tar: $(code_formatter_dir)Dockerfile $(code_formatter_dir).modified-files.tar $(code_formatter_dir).editorconfig $(code_formatter_dir).flake8 $(code_formatter_dir).prettierrc $(code_formatter_dir).eslintrc.json $(code_formatter_dir).stylelintrc.json
	@rm -f $@
	@$(DOCKER) image rm puzzlemassive-code-formatter-files 2> /dev/null || printf ""
	DOCKER_BUILDKIT=1 $(DOCKER) build -f $(code_formatter_dir)Dockerfile \
		--build-arg LINT_AUTO_FIX=yes \
		--target output-files \
		-t puzzlemassive-code-formatter-files \
		--output type=tar,dest=$@ \
		$(code_formatter_dir)
	@echo ""
	-tar t -f $@
	@echo ""
	@echo "Overwrite files in project directory with the changed files from $@ file? [y/n]"
	@read -r overwrite_files_confirm && if [ "$$overwrite_files_confirm" = "y" ]; then tar x -f $@ --overwrite; fi
	touch $@
.PHONY: clean
clean:
	rm $(objects)
