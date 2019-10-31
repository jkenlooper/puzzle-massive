-- This is used for checking if the name is unique and if it has been approved
-- (accepted) or rejected.  The approved_date can be set in the future to
-- auto-approve without having to manually do it from an admin interface.
-- When the approved_date is null treat the name as rejected.
create table NameRegister (
    id integer primary key,
    user integer unique default null,
    display_name text not null, -- should match name except preserves letter case
    name text unique not null, -- stored as all lowercase
    approved integer default 0,
    approved_date text default null,
    foreign key ( user ) references User ( id ) on delete set null
);


