SELECT p.puzzle_id, p.pieces, p.link, p.description, p.bg_color, p.m_date FROM Puzzle as p
WHERE permission = 0 AND status = 1 ORDER BY m_date DESC LIMIT 1;
