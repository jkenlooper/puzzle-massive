concat_configs := $(shell find src -name '*.concat')
concat_files := $(concat_configs:%.concat=%)

objects := $(concat_files) .minifycss .minifycss-prerequisites .minifyhtml dist/puzzle-pieces.min.js

# clear out any suffixes
.SUFFIXES:

# Allow use of automatic variables in prerequisites
.SECONDEXPANSION:

all :  $(objects) $(concat_configs)
.PHONY : all clean


# Concat task
# The .concat files list the files that will be combined into the target file.
# For example: test.js is built from the files listed in test.js.concat.
% : %.concat
	@echo "Combining files listed in $< to $@";
	@rm -f $@;
	@cat $< | xargs cat >> $@;

# Touch .concat files to trigger rebuilding based on their prerequisites.
$(concat_configs) : %: $$(shell cat $$@)
	@touch $@;

.minifycss : $(shell npm run minifycss-prerequisites 2> /dev/null > /dev/null && cat .minifycss-prerequisites)
	npm run minifycss;
	@touch .minifycss;

.minifyhtml : src/puzzle-pieces.html
	npm run minifyhtml;
	@touch .minifyhtml;

dist/puzzle-pieces.min.js : src/puzzle-pieces.tmp.js
	npm run minifyjs;

# Automate marking all files that have been created to be ignored by git.
built_cache_index_files = $(filter $(shell git ls-files), $(sort $(objects)))

# Remove all built files except those that are tracked by git (built_cache_index_files).
clean :
	rm -rf $(sort $(filter-out $(built_cache_index_files),$(objects) ))
