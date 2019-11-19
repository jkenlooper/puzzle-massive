-- Stores the player information and other settings.
create table PlayerAccount (
  id integer primary key,
  user integer not null,
  email text, -- email is not unique, but only one unique email should be marked as verified
  email_verified integer default 0,
  email_verify_token text,
  email_verify_token_expire text, -- datetime that email_verify_token is invalid
  reset_login_token text,
  reset_login_token_expire text, -- datetime that reset_login_token is invalid
  foreign key ( user ) references User ( id ) on delete cascade
);

