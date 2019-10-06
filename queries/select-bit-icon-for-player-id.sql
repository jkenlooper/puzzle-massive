select b.name as icon, u.id as player
from User as u
left outer join BitIcon as b on (b.user = u.id)
where u.id = :player_id;
