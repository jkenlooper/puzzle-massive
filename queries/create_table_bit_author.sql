CREATE TABLE BitAuthor (
  id INTEGER PRIMARY KEY,
  name TEXT, -- first and last name
  slug_name TEXT unique, -- name that is suitable in URLs
  artist_document TEXT -- file name ending with .md
);
