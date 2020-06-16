select
pf.id as puzzle_file_id,
pf.url,
a.id as attribution_id,
a.title,
a.author_link,
a.author_name,
a.source,
l.source as license_source,
l.name as license_name,
l.title as license_title
from PuzzleFile as pf
join Attribution as a on (a.id = pf.attribution)
join License as l on (l.id = a.license)
where pf.puzzle = :puzzle and pf.name = :name;
