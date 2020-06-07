update Piece set
adjacent = :adjacent,
b = :b,
col = :col,
h = :h,
parent = :parent,
r = :r,
rotate = :rotate,
row = :row,
status = :status,
w = :w,
x = :x,
y = :y
where puzzle = :puzzle and id = :id;
