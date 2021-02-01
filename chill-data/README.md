# Chill Data

Site specific content that is not part of the main Puzzle Massive project. This
is where content can go and not be included in the source code of puzzle-massive
repo.

The [create-db-dump-sql.sh](../bin/create-db-dump-sql.sh) script will recursively
find any file within this folder that matches `chill-*.yaml`.

This script also loads the [styleguide.yaml](styleguide.yaml) if in the 'development'
environment.

## Other Templates, Queries, and Documents

Within each templates, queries, and documents directory there is an 'other'
directory that can be used for site specific files. These are not included in
the Puzzle Massive source code.
