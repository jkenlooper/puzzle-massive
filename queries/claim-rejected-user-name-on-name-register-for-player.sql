update NameRegister set user = :player_id,
approved = 1,
approved_date = datetime('now')
where name = :name
and user is null
and approved_date is null
;
