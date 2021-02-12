-- See issue #25 for puzzle types that explain variants and features
-- This table is populated based on the queries/puzzle-feature--*.sql files.
-- 1. A descriptive name of this feature to show
-- 2. Description text which will be used in meta description and other places
-- 3. Features are enabled only if the site.cfg PUZZLE_FEATURE includes the slug
create table PuzzleFeature (
    id integer primary key,
    slug text unique not null,
    name text, -- 1
    description text, -- 2
    enabled integer default 0 -- 3
);
