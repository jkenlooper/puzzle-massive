CREATE TABLE License (
    id INTEGER PRIMARY KEY,
    source, -- link to page for license information
    name unique,
    title -- Unsplash, Creative Commons Attribution 4.0 Interanational License, etc.
);
