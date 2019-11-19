update PlayerAccount set email_verify_token = :email_verify_token, email_verify_token_expire = datetime('now', :expire_token_timeout) where user = :player_id;
