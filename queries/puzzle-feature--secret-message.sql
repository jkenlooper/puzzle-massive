insert into PuzzleFeature (
    slug,
    name,
    description
) values (
    "secret-message",
    "Secret Message",
    "Show a message when the puzzle is completed."
) on conflict (slug) do
update set
name = excluded.name,
description = excluded.description
;
