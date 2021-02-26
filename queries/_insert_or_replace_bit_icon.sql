INSERT INTO BitIcon (author, name) VALUES (:author, :name)
on conflict (name) do update set
author = excluded.author,
name = excluded.name
;
