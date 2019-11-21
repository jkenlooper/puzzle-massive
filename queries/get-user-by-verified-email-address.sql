select user from PlayerAccount
where email = :email
and email_verified = 1
;
