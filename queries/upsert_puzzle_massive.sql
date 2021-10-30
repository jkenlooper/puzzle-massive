insert or replace into PuzzleMassive (
    key,
    label,
    description,
    intvalue,
    textvalue,
    blobvalue
) values (
    :key,
    :label,
    :description,
    :intvalue,
    :textvalue,
    :blobvalue
)
on conflict (key) do update set
label = :label,
description = :description,
intvalue = :intvalue,
textvalue = :textvalue,
blobvalue = :blobvalue
where key = :key
;

