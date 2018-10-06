
-- File generated with SQLiteStudio v3.0.7 on Fri Nov 25 18:16:07 2016
--
-- Text encoding used: UTF-8
--
-- Results of query:
-- select * from Piece where puzzle in (255, 264)                    
--
/*
grouped
:8:672:462:90:8:
:1:802:462:::
:11:737:462:::

grouped
:3:704:711:0:3:
:2:769:711:::

grouped
:9:495:722:180:10:
:10:495:657:::

not grouped
:5:194:707:0::
:7:40:726:180::
:6:183:530:0::
:0:46:522:270::
*/

--CREATE TABLE Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg);
-- group 8
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (8, 255, 672, 462, 90, 0, 1, 0, 8, '4.3', '8.2', '8.3', '8.4', NULL, 'light', 104, 104, 1, '11:65,0 4:0,-65 7:0,65');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (1, 255, 802, 462, 0, 0, 1, 2, 8, '5.3', '1.2', '1.3', '11.2', NULL, 'light', 104, 104, 1, '10:0,65 11:-65,0 5:0,-65');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (11, 255, 737, 462, 90, 180, 1, 1, 8, '6.3', '11.2', '11.3', '8.2', NULL, 'light', 104, 104, 1, '0:0,65 8:-65,0 6:0,-65 1:65,0');

-- group 3
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (3, 255, 704, 711, 0, 0, 3, 0, 3, '7.3', '3.2', '3.3', '3.4', NULL, 'light', 104, 104, 1, '2:65,0 7:0,-65');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (2, 255, 769, 711, 270, 90, 3, 1, 3, '0.3', '2.2', '2.3', '3.2', NULL, 'light', 104, 104, 1, '0:0,-65 9:65,0 3:-65,0');

-- group 10 
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (9, 255, 495, 722, 180, 180, 3, 2, 10, '10.3', '9.2', '9.3', '2.2', NULL, 'light', 104, 104, 1, '10:0,-65 2:-65,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (10, 255, 495, 657, 0, 180, 2, 2, 10, '1.3', '10.2', '10.3', '0.2', NULL, 'light', 104, 104, 1, '0:-65,0 9:0,65 1:0,-65');

-- group 4 (top left piece)
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (4, 255, 363, 218, 180, 180, 0, 0, 4, '4.1', '4.2', '4.3', '4.4', 1, 'light', 104, 104, 1, '8:0,65 6:65,0');

-- not grouped pieces
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (5, 255, 194, 707, 0, 270, 0, 2, NULL, '5.1', '5.2', '5.3', '6.2', NULL, 'light', 104, 104, 1, '1:0,65 6:-65,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (7, 255, 40,  726, 180, 90, 2, 0, NULL, '8.3', '7.2', '7.3', '7.4', NULL, 'light', 104, 104, 1, '8:0,-65 0:65,0 3:0,65');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (6, 255, 183, 530, 0, 0, 0, 1, NULL, '6.1', '6.2', '6.3', '4.2', NULL, 'light', 104, 104, 1, '11:0,65 4:-65,0 5:65,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (0, 255, 46, 522, 270, 90, 2, 1, NULL, '11.3', '0.2', '0.3', '7.2', NULL, 'light', 104, 104, 1, '2:0,65 11:0,-65 10:65,0 7:-65,0');


-- the other puzzle
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (9, 264, 301, 250, 90, 270, 0, 0, 9, '9.1', '9.2', '9.3', '9.4', 1, 'light', 102, 102, 1, '4:64,0 20:0,64');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (4, 264, 741, 5, 90, 180, 0, 1, NULL, '4.1', '4.2', '4.3', '9.2', NULL, 'dark', 102, 102, 0, '9:-64,0 12:64,0 6:0,64');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (12, 264, 293, 249, 0, 0, 0, 2, NULL, '12.1', '12.2', '12.3', '4.2', NULL, 'dark', 102, 102, 0, '4:-64,0 22:0,64 23:64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (23, 264, 757, 203, 270, 180, 0, 3, NULL, '23.1', '23.2', '23.3', '12.2', NULL, 'light', 102, 102, 1, '17:64,0 11:0,64 12:-64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (17, 264, 647, 622, 0, 270, 0, 4, NULL, '17.1', '17.2', '17.3', '23.2', NULL, 'light', 102, 102, 1, '0:0,64 23:-64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (20, 264, 647, 193, 90, 180, 1, 0, NULL, '9.3', '20.2', '20.3', '20.4', NULL, 'light', 102, 102, 1, '9:0,-64 6:64,0 15:0,64');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (6, 264, 169, 712, 0, 180, 1, 1, NULL, '4.3', '6.2', '6.3', '20.2', NULL, 'dark', 102, 102, 0, '20:-64,0 3:0,64 4:0,-64 22:64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (22, 264, 157, 744, 90, 90, 1, 2, NULL, '12.3', '22.2', '22.3', '6.2', NULL, 'dark', 102, 102, 0, '18:0,64 11:64,0 12:0,-64 6:-64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (11, 264, 339, 114, 90, 90, 1, 3, NULL, '23.3', '11.2', '11.3', '22.2', NULL, 'light', 102, 102, 1, '0:64,0 23:0,-64 22:-64,0 7:0,64');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (0, 264, 904, 242, 0, 270, 1, 4, NULL, '17.3', '0.2', '0.3', '11.2', NULL, 'light', 102, 102, 1, '17:0,-64 10:0,64 11:-64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (15, 264, 840, 190, 90, 180, 2, 0, NULL, '20.3', '15.2', '15.3', '15.4', NULL, 'light', 102, 102, 1, '3:64,0 20:0,-64 21:0,64');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (3, 264, 526, 533, 270, 180, 2, 1, NULL, '6.3', '3.2', '3.3', '15.2', NULL, 'light', 102, 102, 1, '18:64,0 13:0,64 6:0,-64 15:-64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (18, 264, 904, 799, 90, 90, 2, 2, NULL, '22.3', '18.2', '18.3', '3.2', NULL, 'dark', 102, 102, 0, '3:-64,0 19:0,64 22:0,-64 7:64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (7, 264, 549, 539, 180, 90, 2, 3, NULL, '11.3', '7.2', '7.3', '18.2', NULL, 'light', 102, 102, 1, '24:0,64 18:-64,0 11:0,-64 10:64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (10, 264, 218, 719, 180, 0, 2, 4, NULL, '0.3', '10.2', '10.3', '7.2', NULL, 'light', 102, 102, 1, '0:0,-64 2:0,64 7:-64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (21, 264, 174, 66, 180, 0, 3, 0, NULL, '15.3', '21.2', '21.3', '21.4', NULL, 'light', 102, 102, 1, '8:0,64 13:64,0 15:0,-64');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (13, 264, 189, 237, 180, 270, 3, 1, NULL, '3.3', '13.2', '13.3', '21.2', NULL, 'dark', 102, 102, 0, '19:64,0 3:0,-64 21:-64,0 14:0,64');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (19, 264, 41, 527, 0, 0, 3, 2, NULL, '18.3', '19.2', '19.3', '13.2', NULL, 'dark', 102, 102, 0, '24:64,0 1:0,64 18:0,-64 13:-64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (24, 264, 112, 22, 180, 0, 3, 3, NULL, '7.3', '24.2', '24.3', '19.2', NULL, 'light', 102, 102, 1, '2:64,0 19:-64,0 5:0,64 7:0,-64');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (2, 264, 103, 247, 0, 270, 3, 4, NULL, '10.3', '2.2', '2.3', '24.2', NULL, 'light', 102, 102, 1, '16:0,64 24:-64,0 10:0,-64');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (8, 264, 664, 131, 0, 180, 4, 0, NULL, '21.3', '8.2', '8.3', '8.4', NULL, 'light', 102, 102, 1, '21:0,-64 14:64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (14, 264, 850, 550, 180, 270, 4, 1, NULL, '13.3', '14.2', '14.3', '8.2', NULL, 'light', 102, 102, 1, '8:-64,0 1:64,0 13:0,-64');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (1, 264, 842, 245, 270, 90, 4, 2, NULL, '19.3', '1.2', '1.3', '14.2', NULL, 'light', 102, 102, 1, '19:0,-64 5:64,0 14:-64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (5, 264, 621, 448, 270, 180, 4, 3, NULL, '24.3', '5.2', '5.3', '1.2', NULL, 'light', 102, 102, 1, '24:0,-64 1:-64,0 16:64,0');
INSERT INTO Piece (id, puzzle, x, y, r, rotate, "row", col, parent, top_path, right_path, bottom_path, left_path, status, bg, w, h, b, adjacent) VALUES (16, 264, 11, 356, 270, 0, 4, 4, NULL, '2.3', '16.2', '16.3', '5.2', NULL, 'light', 102, 102, 1, '2:0,-64 5:-64,0');

