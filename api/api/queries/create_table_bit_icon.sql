CREATE TABLE BitIcon (
  id INTEGER PRIMARY KEY,
  user INTEGER REFERENCES User (id),
  author INTEGER REFERENCES BitAuthor (id),
  name TEXT UNIQUE, -- should match the filename without extension (character-fish)
  last_viewed TEXT, -- timestamp
  expiration TEXT -- timestamp
);
