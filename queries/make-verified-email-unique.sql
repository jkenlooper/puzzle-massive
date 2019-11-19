update PlayerAccount set email = null, email_verify_token = null, email_verify_token_expire = null
where user != :player_id
and email_verified = 0
and email = :email
;
