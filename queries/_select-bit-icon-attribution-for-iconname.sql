select ba.name as artist_name,
ba.slug_name as slug_name
from BitIcon as bi
join BitAuthor as ba on (bi.author = ba.id)
where bi.name = :iconname
;
