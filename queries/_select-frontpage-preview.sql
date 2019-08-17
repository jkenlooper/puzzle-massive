SELECT p.id, pf.name, pf.url, p.puzzle_id, p.pieces, p.table_width, p.table_height, p.link, p.description, p.bg_color, p.m_date, p.status, p.permission, pf.attribution,
p.owner,
p1.puzzle_id as original_puzzle_id,
pv.name as puzzle_variant_name,

-- Find the short and long dimensions of the preview img by checking the table_width
-- and table_height since the img width and height is not currently stored.
round((min(CAST(p.table_width AS float), CAST(p.table_height AS float)) / max(CAST(p.table_width AS float), CAST(p.table_height AS float))) * 384) AS short,
384.0 AS long,

strftime('%Y-%m-%d %H:%M', p.m_date, '+7 hours') as redo_date,
strftime('%s', p.m_date) >= strftime('%s', 'now', '-7 hours') as is_recent,
pi.original == pi.instance as is_original,

strftime('%s','now') - strftime('%s', p.m_date) as seconds_from_now
 FROM Puzzle AS p
JOIN PuzzleFile AS pf ON (pf.puzzle = p1.id) -- Get the original
JOIN PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (p1.id = pi.original)
JOIN PuzzleVariant as pv on (pi.variant = pv.id)
WHERE pf.name == 'preview_full'
AND p.puzzle_id = :puzzle_id
GROUP BY p.id
