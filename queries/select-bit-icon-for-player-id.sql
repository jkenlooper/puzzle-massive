select b.name as icon, u.id as player,
nr.display_name as name, nr.approved as name_approved
from User as u
left outer join NameRegister as nr on (nr.user = u.id)
left outer join BitIcon as b on (b.user = u.id)
where u.id = :player_id;
