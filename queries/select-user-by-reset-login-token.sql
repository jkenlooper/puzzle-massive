select
user,
reset_login_token,
email_verified == 1 and reset_login_token_expire and reset_login_token_expire > datetime('now') as has_active_reset_login_token
from PlayerAccount
where reset_login_token = :token;
