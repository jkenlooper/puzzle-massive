SELECT p.id, p.puzzle_id, p.permission, p.status, p.pieces, p.link, p.description, p.bg_color, p.m_date, p.owner

FROM Puzzle AS p

-- SUGGESTED
where p.status == -20
GROUP BY p.id
ORDER BY p.m_date
;
