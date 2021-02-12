-- Puzzle features are added individually for now.
-- See the queries/puzzle-feature--*.sql files and the bin/create-db-dump-sql.sh
-- script.
insert into PuzzleFeature (
    slug,
    name,
    description
) values (
    :slug,
    :name,
    :description
) on conflict (slug) do
update set
name = excluded.name,
description = excluded.description
;
