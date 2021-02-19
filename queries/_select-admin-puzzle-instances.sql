SELECT p.id,
pf.name,
pf.url,
p.puzzle_id,
p.permission,
p.pieces,
p.table_width,
p.table_height,
p.link,
p.description,
p.bg_color,
p.m_date,
pfd.puzzle_feature is not null as has_hidden_preview,

-- Find the short and long dimensions of the preview img by checking the table_width
-- and table_height since the img width and height is not currently stored.
round((min(CAST(p.table_width AS float), CAST(p.table_height AS float)) / max(CAST(p.table_width AS float), CAST(p.table_height AS float))) * 128) AS short,
128.0 AS long

FROM Puzzle AS p
JOIN PuzzleInstance as pi on (pi.instance = p.id)
left outer join Puzzle as p1 on (p1.id = pi.original)
left outer join PuzzleFile AS pf ON (pf.puzzle = p1.id and pf.name = 'preview_full') -- Get the original
left outer join PuzzleFeature as pzf on (pzf.slug = 'hidden-preview' and pzf.enabled = 1)
left outer join PuzzleFeatureData as pfd on (pfd.puzzle = p.id and pfd.puzzle_feature = pzf.id)

where p.id != pi.original -- Only the puzzle instances
and p.status in (1, 2, 3, 4, 5, -3, -5, -6, -7, -30)

GROUP BY p.id
ORDER BY p.m_date
;
