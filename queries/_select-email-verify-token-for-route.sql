select :token as token
from PlayerAccount as pa
where :token = pa.email_verify_token
and pa.email_verified = 0
and pa.email_verify_token_expire is not null
and pa.email_verify_token_expire > datetime('now')
;
