update NameRegister set approved = 1
where approved_date is not null
and user is not null
and approved_date < datetime('now')
and approved = 0;
