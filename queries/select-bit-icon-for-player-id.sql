select b.name as icon, u.id as player,
u.name, u.name_approved
from User as u
left outer join BitIcon as b on (b.user = u.id)
where u.id = :player_id;
