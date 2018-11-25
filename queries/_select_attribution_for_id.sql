select a.title,
a.author_link,
a.author_name,
a.source,
l.source as license_source,
l.name as license_name,
l.title as license_title
from Attribution as a
join License as l on (l.id = a.license)
where a.id = :attribution_id;
