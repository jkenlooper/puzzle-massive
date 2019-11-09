insert into NameRegister (user, name, display_name, approved_date) values (:player_id, :name, :display_name, datetime('now', :time));
