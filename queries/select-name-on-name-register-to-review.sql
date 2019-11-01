select * from NameRegister
where approved = 0
and approved_date is not null
order by approved_date;
