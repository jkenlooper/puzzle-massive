CREATE TABLE Attribution (
    id INTEGER PRIMARY KEY,
    title, -- title of work
    author_link, -- link to author's profile page
    author_name,
    source, -- link to page showing the image
    license INTEGER REFERENCES License (id)
);
