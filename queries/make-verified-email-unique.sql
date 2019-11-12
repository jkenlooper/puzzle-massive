update PlayerAccount set email = null, email_verify_token = null, reset_login_token = null
where user != :player_id
and email_verified = 0
and email = :email
;
