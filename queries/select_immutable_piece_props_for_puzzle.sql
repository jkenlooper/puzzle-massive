select
    adjacent,
    b,
    h,
    id,
    rotate,
    w
from Piece where (puzzle = :puzzle);
