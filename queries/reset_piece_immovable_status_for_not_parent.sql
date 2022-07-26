update Piece set status = null
where puzzle = :puzzle
and parent != :parent
and status = 1
;
