select
u.id,
pa.email, pa.email_verified,
pa.email_verify_token,
pa.email_verified == 0 and pa.email_verify_token_expire and pa.email_verify_token_expire > datetime('now') as is_verifying_email,
pa.reset_login_token,
pa.email_verified == 1 and pa.reset_login_token_expire and pa.reset_login_token_expire > datetime('now') as has_active_reset_login_token
from User as u
left outer join PlayerAccount as pa on (pa.user = u.id)
where u.id = :player_id;
