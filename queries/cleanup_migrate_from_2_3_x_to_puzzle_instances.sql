-- For migrate_from_2_3_x_to_puzzle_instances.py if running multiple times.
drop table IF EXISTS PuzzleVariant;
drop table IF EXISTS PuzzleInstance;
drop table IF EXISTS User_Puzzle;
