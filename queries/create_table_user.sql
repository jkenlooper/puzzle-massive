create table User(id integer primary key,
    points integer,
    score integer,
    icon, -- TODO: remove icon. It is no longer used.
    login,
    password,
    m_date,
    cookie_expires,
    ip);
