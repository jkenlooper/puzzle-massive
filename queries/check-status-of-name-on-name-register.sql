select
user,
name,
display_name,
approved,
user is not null as claimed,
approved_date is null as rejected
from NameRegister
where name = :name;
