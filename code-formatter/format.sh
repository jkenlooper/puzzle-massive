#!/usr/bin/env sh

modified_files_prettier_client_side_public_src=$(find . \( -newer .last-modified/client-side-public-src -type f -path './client-side-public/src/*' \) \( -name '*.js' -o -name '*.css' -o -name '*.md' -o -name '*.html' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' \))
if [ -n "$modified_files_prettier_client_side_public_src" ]; then
  npm run prettier -- --write $modified_files_prettier_client_side_public_src
  echo "$(date)" > .last-modified/client-side-public-src
fi

modified_files_prettier_design_tokens_src=$(find . \( -newer .last-modified/design-tokens-src -type f -path './design-tokens/src/*' \) \( -name '*.js' -o -name '*.css' -o -name '*.md' -o -name '*.html' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' \))
if [ -n "$modified_files_prettier_design_tokens_src" ]; then
  npm run prettier -- --write $modified_files_prettier_design_tokens_src
  echo "$(date)" > .last-modified/design-tokens-src
fi

modified_files_prettier_mockups=$(find . \( -newer .last-modified/mockups -type f -path './mockups/*' \) \( -name '*.js' -o -name '*.css' -o -name '*.md' -o -name '*.html' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' \))
if [ -n "$modified_files_prettier_mockups" ]; then
  npm run prettier -- --write $modified_files_prettier_mockups
  echo "$(date)" > .last-modified/mockups
fi

modified_files_prettier_root=$(find . \( -newer .last-modified/root -type f -path './root/*' \) \( -name '*.js' -o -name '*.css' -o -name '*.md' -o -name '*.html' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' \))
if [ -n "$modified_files_prettier_root" ]; then
  npm run prettier -- --write $modified_files_prettier_root
  echo "$(date)" > .last-modified/root
fi

modified_files_prettier_docs=$(find . \( -newer .last-modified/docs -type f -path './docs/*' \) \( -name '*.md' -o -name '*.html' \))
if [ -n "$modified_files_prettier_docs" ]; then
  npm run prettier -- --write $modified_files_prettier_docs
  echo "$(date)" > .last-modified/docs
fi

modified_files_prettier_documents=$(find . \( -newer .last-modified/documents -type f -path './documents/*' \) \( -name '*.md' -o -name '*.html' \))
if [ -n "$modified_files_prettier_documents" ]; then
  npm run prettier -- --write $modified_files_prettier_documents
  echo "$(date)" > .last-modified/documents
fi

modified_files_prettier_queries=$(find . \( -newer .last-modified/queries -type f -path './queries/*' \) \( -name '*.md' -o -name '*.html' \))
if [ -n "$modified_files_prettier_queries" ]; then
  npm run prettier -- --write $modified_files_prettier_queries
  echo "$(date)" > .last-modified/queries
fi

modified_files_prettier_templates=$(find . \( -newer .last-modified/templates -type f -path './templates/*' \) \( -name '*.md' -o -name '*.html' \))
if [ -n "$modified_files_prettier_templates" ]; then
  npm run prettier -- --write $modified_files_prettier_templates
  echo "$(date)" > .last-modified/templates
fi

modified_files_black_api=$(find . \( -newer .last-modified/api -type f -path './api/*' \) -name '*.py')
if [ -n "$modified_files_black_api" ]; then
  black api/
  echo "$(date)" > .last-modified/api
fi

modified_files_black_divulger=$(find . \( -newer .last-modified/divulger -type f -path './divulger/*' \) -name '*.py')
if [ -n "$modified_files_black_divulger" ]; then
  black divulger/
  echo "$(date)" > .last-modified/divulger
fi

modified_files_black_enforcer=$(find . \( -newer .last-modified/enforcer -type f -path './enforcer/*' \) -name '*.py')
if [ -n "$modified_files_black_enforcer" ]; then
  black enforcer/
  echo "$(date)" > .last-modified/enforcer
fi

modified_files_black_stream=$(find . \( -newer .last-modified/stream -type f -path './stream/*' \) -name '*.py')
if [ -n "$modified_files_black_stream" ]; then
  black stream/
  echo "$(date)" > .last-modified/stream
fi
