select * from NameRegister
where approved_date is not null
and approved = 0
order by approved_date;
