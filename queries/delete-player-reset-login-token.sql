update PlayerAccount set reset_login_token = null, reset_login_token_expire = null
where user = :user;
