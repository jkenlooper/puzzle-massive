CREATE TABLE PuzzleInstance (
    original integer not null,
    instance integer not null, -- is same as original if it is the original
    variant integer not null,
    foreign key ( original ) references Puzzle ( id ),
    foreign key ( instance ) references Puzzle ( id ),
    foreign key ( variant ) references PuzzleVariant ( id )
);
