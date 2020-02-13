update User set
password = :password,
m_date = datetime('now'),
cookie_expires = strftime('%Y-%m-%d', 'now', '+14 days')
where ip = :ip and id = :id and password isnull;
