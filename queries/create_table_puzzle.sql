CREATE TABLE Puzzle (
    id integer PRIMARY KEY,
    puzzle_id,
    pieces integer,
    rows integer,
    cols integer,
    piece_width,
    mask_width,
    table_width DEFAULT 960,
    table_height DEFAULT 600,
    name,
    link,
    description,
    bg_color,
    m_date,
    owner, -- TODO: set as integer
    queue integer DEFAULT 0,
    status,
    permission
);
