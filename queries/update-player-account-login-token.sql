update PlayerAccount set reset_login_token = :reset_login_token, reset_login_token_expire = datetime('now', :expire_token_timeout) where user = :player_id;
