INSERT INTO BitAuthor (name, slug_name, artist_document) VALUES (:name, :slug_name, :artist_document)
on conflict (slug_name) do update set
name=excluded.name,
artist_document=excluded.artist_document
;
