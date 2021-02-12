-- See issue #25 for puzzle types that explain variants and features
-- hidden preview image #80
-- secret message #80 (4)
-- sponsored puzzes #79 (4, 5)
-- territories #58 (5, 6)
-- tangram puzzles #55 ()
-- puzzle of the day #38 #80 (3)
-- hide pieces #32 (6)
-- hoard pieces #32 (5, 6)
-- invite only #17 (5)
-- last player standing #13 (3, 5, 6, 7)
-- massive monday #12 (3, 4, 5)
-- advent puzzle invite only #10 (3, 5, 6)
-- start/end time configurable #5 (3)
-- rotatable pieces #52 ()
--
-- 3. Some features may use start and stop datetime values
-- 4. A text message that is used by some features
-- 5. Players can be a comma separated list of player ids or other formats
-- 6. Pieces can be a comma separated list of piece ids or other formats
-- 7. An integer for general use could be for enable/disable, limit count, etc.
create table PuzzleFeatureData (
    id integer primary key,
    puzzle integer not null,
    puzzle_feature integer not null,
    start_time text, -- 3
    stop_time text, -- 3
    message text, -- 4
    players text, -- 5
    pieces text, -- 6
    n integer default 0 not null, -- 7
    foreign key ( puzzle ) references Puzzle ( id ) on delete cascade,
    foreign key ( puzzle_feature ) references PuzzleFeature ( id ) on delete cascade,
    unique (puzzle, puzzle_feature) on conflict replace
);
