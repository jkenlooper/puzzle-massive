select pf.url as pageimage,
printf('/chill/site/front/%s/', :puzzle_id) as canonical_path,
p.table_width as pageimage_table_width,
p.table_height as pageimage_table_height,

-- Find the short and long dimensions of the preview img by checking the table_width
-- and table_height since the img width and height is not currently stored.
round((min(CAST(p.table_width AS float), CAST(p.table_height AS float)) / max(CAST(p.table_width AS float), CAST(p.table_height AS float))) * 384) AS pageimage_short,
384.0 AS pageimage_long

from Puzzle as p
join PuzzleFile as pf on (pf.puzzle = p1.id) -- Get the original
join PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (p1.id = pi.original)
where pf.name == 'preview_full'
and p.puzzle_id = :puzzle_id
group by p.id;
