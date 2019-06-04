CREATE TABLE PuzzleVariant (
    id integer primary key,
    slug text unique,
    name text unique,
    description text
);
