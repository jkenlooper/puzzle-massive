select :token as token
from PlayerAccount as pa
where :token = pa.reset_login_token
and pa.email_verified = 1
and pa.reset_login_token_expire is not null
and pa.reset_login_token_expire > datetime('now')
;
pa.reset_login_token,
pa.email_verified == 1 and pa.reset_login_token_expire and pa.reset_login_token_expire > datetime('now') as has_active_reset_login_token
