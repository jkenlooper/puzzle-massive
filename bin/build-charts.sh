#!/usr/bin/env bash

set -o errexit

base_mermaid_config=docs/mermaid-config.json

potential_markdown_files=$(find {api,chill,stream,docs,design-tokens,divulger,enforcer,mockups,source-media,web,_infra,*.md} \
    -type f -name '*.md' \
    ! -path '_infra/.terraform/*')

targets=$(grep -e '```mermaid' --files-with-matches $potential_markdown_files)

for f in $targets; do
    mermaid_config=$base_mermaid_config
    if [ -f $f.mermaid-config.json ]; then
        mermaid_config=$(mktemp)
        jq --slurp '. | .[0] + .[1]' $base_mermaid_config $f.mermaid-config.json > $mermaid_config
    fi
    npm run mmdc -- --configFile $mermaid_config --input $f
done
