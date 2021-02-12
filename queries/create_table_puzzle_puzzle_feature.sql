-- TODO: maybe don't need a linking table
CREATE TABLE Puzzle_PuzzleFeature (
    puzzle integer not null,
    puzzle_feature integer not null,
    puzzle_feature_data integer,
    foreign key ( puzzle ) references Puzzle ( id ) on delete cascade,
    foreign key ( puzzle_feature ) references PuzzleFeature ( id ) on delete cascade,
);
