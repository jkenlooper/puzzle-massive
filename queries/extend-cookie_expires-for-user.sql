update User set cookie_expires = strftime('%Y-%m-%d', 'now', '+14 days') where id = :id;
