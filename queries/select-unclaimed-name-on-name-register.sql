select * from NameRegister
where user is null
and name = :name;
