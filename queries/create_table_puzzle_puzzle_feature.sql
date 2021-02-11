CREATE TABLE Puzzle_PuzzleFeature (
    puzzle integer not null,
    puzzle_feature integer not null,
    puzzle_feature_data integer,
    foreign key ( puzzle ) references Puzzle ( id ) on delete cascade,
    foreign key ( puzzle_feature ) references PuzzleFeature ( id ) on delete cascade,
    foreign key ( puzzle_feature_data ) references PuzzleFeatureData ( id ) on delete set null
);
