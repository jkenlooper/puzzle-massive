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
