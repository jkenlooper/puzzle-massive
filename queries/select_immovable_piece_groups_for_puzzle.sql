select distinct parent from Piece where
puzzle = :puzzle
and status = 1 -- immovable
;
