-- ignore potential errors if the email is not unique
update or ignore PlayerAccount set email = :email where user = :player_id;
