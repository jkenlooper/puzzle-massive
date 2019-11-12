select
u.id,
pa.email, pa.email_verified,
pa.email_verify_token,
pa.email_verified == 0 and pa.reset_login_token and pa.reset_login_token > datetime('now') as is_verifying_email
from User as u
left outer join PlayerAccount as pa on (pa.user = u.id)
where u.id = :player_id;
