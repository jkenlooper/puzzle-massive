-- For migrate_from_2_3_2_to_2_4_0.py if running multiple times.
drop table IF EXISTS PuzzleVariant;
drop table IF EXISTS PuzzleInstance;
drop table IF EXISTS User_Puzzle;
drop table IF EXISTS PlayerAccount;
drop table IF EXISTS NameRegister;
