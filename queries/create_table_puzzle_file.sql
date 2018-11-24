create table PuzzleFile (
    id integer primary key,
    puzzle integer references Puzzle (id) on delete cascade,
    attribution integer references Attribution (id),
    name text,
    url text
);
