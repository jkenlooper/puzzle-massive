alter table BitAuthor add column
slug_name TEXT unique
;
-- Update the two authors
--update BitAuthor set slug_name = 'martin-berube' where id = 1;
--update BitAuthor set slug_name = 'mackenzie-deragon' where id = 2;
