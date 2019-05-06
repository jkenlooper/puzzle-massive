SELECT user, name as icon, expiration > datetime('now') as active
from BitIcon;
-- TODO: add where id in list of ids
