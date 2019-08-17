select b.name as icon from User as u
join BitIcon as b on (b.user = u.id)
where u.id = :player_id;
