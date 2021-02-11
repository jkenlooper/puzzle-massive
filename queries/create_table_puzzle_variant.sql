-- See issue #25 for puzzle types that explain variants and features
CREATE TABLE PuzzleVariant (
    id integer primary key,
    slug text unique,
    name text unique,
    description text
);
