-- Puzzle features are added individually for now.
-- See the queries/puzzle-feature--*.sql files and the
-- api/api/update_enabled_puzzle_features.py script.
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
