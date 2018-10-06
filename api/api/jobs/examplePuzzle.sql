--
-- File generated with SQLiteStudio v3.0.7 on Wed Nov 16 06:09:03 2016
--
-- Text encoding used: UTF-8
--
-- Results of query:
-- select * from Puzzle where id in (255, 264)
--
--BEGIN TRANSACTION;

--CREATE TABLE Puzzle (id, puzzle_id, pieces, rows, cols, piece_width, mask_width, table_width, table_height, name, link, description, bg_color, m_date, owner, queue, status, permission);
INSERT INTO Puzzle (id, puzzle_id, pieces, rows, cols, piece_width, mask_width, table_width, table_height, name, link, description, bg_color, m_date, owner, queue, status, permission) VALUES (255, '3302cf7b7685b', 12, 4, 3, 65, 104, 960, 735, 'photo-1417722009592-65fa261f5632.jpeg', '', '3', '#484662', '2016-11-16 12:42:03', 766, 253, 2, 0);
INSERT INTO Puzzle (id, puzzle_id, pieces, rows, cols, piece_width, mask_width, table_width, table_height, name, link, description, bg_color, m_date, owner, queue, status, permission) VALUES (264, '341973f464f55', 25, 5, 5, 64, 102, 960, 858, 'original-100.jpg', '', '', '#C3FF00', '2016-10-22 15:35:57', 767, 261, 2, 0);

--COMMIT TRANSACTION;
--PRAGMA foreign_keys = on;
