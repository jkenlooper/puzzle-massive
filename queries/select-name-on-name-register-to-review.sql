select * from NameRegister
where approved_date is not null
and approved_date > datetime('now', '-3 days')
and user is not null
order by approved_date;
