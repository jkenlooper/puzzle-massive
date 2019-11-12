-- ignore potential errors if the email is not unique
update PlayerAccount set email = :email where user = :player_id;
