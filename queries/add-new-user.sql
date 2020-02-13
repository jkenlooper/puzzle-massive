insert into User
(password, m_date, cookie_expires, points, score, login, ip) values
(:password, datetime('now'), strftime('%Y-%m-%d', 'now', '+14 days'), :points, 0, :login, :ip);
