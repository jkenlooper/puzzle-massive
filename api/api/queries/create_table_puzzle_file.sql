create table PuzzleFile (
    id integer primary key,
    puzzle integer references Puzzle (id) on delete cascade,
    name text,
    url text
);
