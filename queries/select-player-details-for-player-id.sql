select
u.id,
pa.email, pa.email_verified
from User as u
left outer join PlayerAccount as pa on (pa.user = u.id)
where u.id = :player_id;
