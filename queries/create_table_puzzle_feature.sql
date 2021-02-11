-- See issue #25 for puzzle types that explain variants and features
-- 1. A descriptive name of this feature to show
-- 2. Description text which will be used in meta description and other places
create table PuzzleFeature (
    id integer primary key,
    slug text unique not null,
    name text, -- 1
    description text, -- 2
);
