create table User(id integer primary key,
    points integer,
    score integer,
    icon, -- TODO: remove icon. It is no longer used.
    login,
    password,
    m_date,
    cookie_expires,
    ip,
    name text, -- TODO: should be unique if table is ever recreated
    name_approved integer default 0
  );

-- existing User table has been altered to add columns:
-- name text, -- can't set to unique when altering table
-- name_approved integer default 0,

