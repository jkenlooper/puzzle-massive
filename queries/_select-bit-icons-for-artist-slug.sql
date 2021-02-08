select bi.name, substr(bi.name, 0, instr(bi.name, '-')) as group_name
from BitAuthor as ba
join BitIcon as bi on (bi.author = ba.id)
where ba.slug_name = :slug_name
;
