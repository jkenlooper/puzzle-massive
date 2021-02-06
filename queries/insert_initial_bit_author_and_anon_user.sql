-- Set the two authors
INSERT INTO BitAuthor (id, name, slug_name, artist_document) VALUES (1, 'Martin Berube', 'martin-berube', 'artists/martin-berube.md');
INSERT INTO BitAuthor (id, name, slug_name, artist_document) VALUES (2, 'Mackenzie Deragon', 'mackenzie-deragon', 'artists/mackenzie-deragon.md');

-- Insert the anonymous player (ANONYMOUS_USER_ID)
INSERT OR IGNORE INTO User (id, login, password, points, score) VALUES (2, 'none', 'none', 0 ,0);
