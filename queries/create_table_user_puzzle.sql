CREATE TABLE User_Puzzle (
    player integer not null,
    puzzle integer unique on conflict fail, -- a null here would mean the player has an open slot
    foreign key ( player ) references User ( id ) on delete cascade,
    foreign key ( puzzle ) references Puzzle ( id ) on delete set null
);
