select id from User indexed by user_ip where ip = :ip and password isnull limit 1;
