select bi.name
from BitAuthor as ba
join BitIcon as bi on (bi.author = ba.id)
where ba.slug_name = :slug_name
;
