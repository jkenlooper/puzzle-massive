-- Stores the player information and other settings.
create table PlayerAccount (
  id integer primary key,
  user integer not null,
  email text unique,
  email_verified integer default 0,
  email_verify_token text,
  reset_login_token text,
  foreign key ( user ) references User ( id ) on delete cascade
);

