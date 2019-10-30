update NameRegister set user = :player_id
where name = :name
and user is null
and approved_date is not null
;
