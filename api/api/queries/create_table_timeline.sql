create table Timeline (
    id integer primary key,
    puzzle integer references Puzzle (id) on delete cascade,
    player integer references User (id),
    message text,
    points integer default 0,
    timestamp date
    );
