update NameRegister set user = :player_id,
display_name = :display_name
where name = :name
and user is null
and approved_date is not null
;
