select
u.id,
b.name as icon,
strftime('%s', b.expiration) <= strftime('%s', 'now') as bit_expired,
u.m_date,
strftime('%s','now') - strftime('%s', u.m_date) as seconds_from_now,
u.points as dots,
u.score,
u.name, u.name_approved,
pa.email, pa.email_verified,
up1.empty_slots_count,
up2.filled_slots_count
from User as u
left outer join PlayerAccount as pa on (pa.user = u.id)
left outer join BitIcon as b on (b.user = u.id)
left outer join (
select count(*) as empty_slots_count, player from User_Puzzle where puzzle is null group by player
) as up1 on (up1.player = u.id)
left outer join (
select count(*) as filled_slots_count, player from User_Puzzle where puzzle is not null group by player
) as up2 on (up2.player = u.id)
where u.id = :player_id;
