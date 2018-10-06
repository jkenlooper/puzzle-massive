SELECT pc.parent FROM Puzzle AS pz
JOIN Piece AS pc ON (pz.id = pc.puzzle)
WHERE pz.puzzle_id = :puzzle_id AND col = 0 AND ROW = 0 AND parent IS NOT NULL;
