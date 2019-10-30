-- TODO: can use upsert?
insert into NameRegister (user, name, approved_date) values (:player_id, :name, datetime('now'));
