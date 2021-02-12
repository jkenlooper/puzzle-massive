insert into PuzzleFeature (
    slug,
    name,
    description
) values (
    "hidden-preview",
    "Hidden Preview Image",
    "Hide the preview image for a puzzle as well as any attribution links that may link to the original image.  Only display the attribution links when puzzle is completed."
) on conflict (slug) do
update set
name = excluded.name,
description = excluded.description
;
