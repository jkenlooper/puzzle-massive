select :token as token
from PlayerAccount as pa
where :token = pa.email_verify_token
and pa.email_verified = 0
and pa.reset_login_token is not null
and pa.reset_login_token > datetime('now')
;
