#!/usr/bin/env sh

set -o errexit

# This file was generated from the code-formatter directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.

mkdir -p .last-modified

set -- design-tokens/src mockups source-media root enforcer queries stream client-side-public/src docs api chill chill-data divulger documents templates

for target in "$@"; do

  set -- js jsx mjs ts tsx css less scss json graphql gql markdown md mdown mkd mkdn mdx vue svelte yml yaml html php rb ruby xml

  for ext in "$@"; do

    # TODO files are not writable because they are bind mounted.
    last_modified_name="$target--prettier-$ext"
    last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
    if [ -e ".last-modified/$last_modified_name" ]; then
      modified_files_prettier="$(find . \
          -newer .last-modified/$last_modified_name \
          -type f -readable -writable \
          -path "./$target/*" \
          -name "*.$ext" \
          -nowarn \
        || printf '')"
    else
      modified_files_prettier="$(find . \
          -type f -readable -writable \
          -path "./$target/*" \
          -name "*.$ext" \
          -nowarn \
        || printf '')"
      touch ".last-modified/$last_modified_name"
    fi
    if [ -n "$modified_files_prettier" ]; then
      npm run prettier -- --write $modified_files_prettier
      echo "$(date)" > ".last-modified/$last_modified_name"
    fi
  done

  last_modified_name="$target--black"
  last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
  if [ -e ".last-modified/$last_modified_name" ]; then
    modified_files_black="$(find . \
        -newer ".last-modified/$last_modified_name" \
        -type f -readable -writable \
        -path "./$target/*" \
        -name '*.py' \
        -nowarn \
      || printf '')"
  else
    modified_files_black="$(find . \
        -type f -readable -writable \
        -path "./$target/*" \
        -name '*.py' \
        -nowarn \
      || printf '')"
    touch ".last-modified/$last_modified_name"
  fi
  if [ -n "$modified_files_black" ]; then
    /usr/local/src/code-formatter/bin/black "$target"
    echo "$(date)" > ".last-modified/$last_modified_name"
  fi
done
