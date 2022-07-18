#!/usr/bin/env sh

set -o errexit

# This file was generated from the code-formatter directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.

set -- design-tokens/src mockups source-media root enforcer queries stream client-side-public/src docs api chill chill-data divulger documents templates

for target in "$@"; do

  set -- js jsx mjs ts tsx css less scss json graphql gql markdown md mdown mkd mkdn mdx vue svelte yml yaml html php rb ruby xml

  if [ -e "$target" ]; then
    for ext in "$@"; do
      modified_files_prettier="$(find "./$target" \
          -type f \
          -name "*.$ext" \
          -nowarn \
        || printf '')"
      if [ -n "$modified_files_prettier" ]; then
        npm run prettier -- --write $modified_files_prettier
      fi
    done

    modified_files_black="$(find "./$target" \
        -type f \
        -name '*.py' \
        -nowarn \
      || printf '')"
    if [ -n "$modified_files_black" ]; then
      /usr/local/src/code-formatter/bin/black "$target"
    fi
  fi

done
