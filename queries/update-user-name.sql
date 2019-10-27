-- ignore potential errors if the name is not unique
update or ignore User set name = :name where id = :player_id;
