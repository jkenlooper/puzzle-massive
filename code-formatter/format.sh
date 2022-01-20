#!/usr/bin/env sh

# This file was generated from the code-formatter directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.


## design-tokens/src

last_modified_name="design-tokens/src"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './design-tokens/src/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './design-tokens/src/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './design-tokens/src/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './design-tokens/src/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black design-tokens/src/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## mockups

last_modified_name="mockups"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './mockups/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './mockups/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './mockups/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './mockups/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black mockups/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## source-media

last_modified_name="source-media"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './source-media/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './source-media/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './source-media/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './source-media/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black source-media/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## root

last_modified_name="root"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './root/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './root/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './root/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './root/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black root/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## enforcer

last_modified_name="enforcer"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './enforcer/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './enforcer/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './enforcer/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './enforcer/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black enforcer/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## queries

last_modified_name="queries"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './queries/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './queries/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './queries/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './queries/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black queries/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## stream

last_modified_name="stream"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './stream/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './stream/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './stream/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './stream/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black stream/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## client-side-public/src

last_modified_name="client-side-public/src"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './client-side-public/src/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './client-side-public/src/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './client-side-public/src/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './client-side-public/src/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black client-side-public/src/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## docs

last_modified_name="docs"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './docs/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './docs/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './docs/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './docs/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black docs/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## api

last_modified_name="api"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './api/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './api/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './api/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './api/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black api/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## chill

last_modified_name="chill"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './chill/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './chill/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './chill/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './chill/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black chill/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## chill-data

last_modified_name="chill-data"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './chill-data/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './chill-data/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './chill-data/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './chill-data/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black chill-data/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## divulger

last_modified_name="divulger"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './divulger/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './divulger/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './divulger/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './divulger/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black divulger/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## documents

last_modified_name="documents"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './documents/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './documents/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './documents/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './documents/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black documents/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## templates

last_modified_name="templates"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './templates/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './templates/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './templates/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './templates/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black templates/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi
