CREATE TABLE PuzzleInstance (
    original integer,
    instance integer,
    variant integer,
    foreign key ( original ) references Puzzle ( id ) on delete cascade,
    foreign key ( instance ) references Puzzle ( id ) on delete cascade,
    foreign key ( variant ) references PuzzleVariant ( id )
);
