-- Delete extra items in PuzzleFile caused when puzzle upload added the
-- preview_full puzzle file twice for unsplash images. The /resources url is not
-- needed when it is an unsplash image (assumed when starting with https).
delete from PuzzleFile
where id in (
        select pf.id
        from Puzzle as p
        join PuzzleFile as pf on (p.id = pf.puzzle and pf.url like '/resources%')
        join PuzzleFile as pf1 on (p.id = pf1.puzzle and pf1.url like 'https%')
        where pf.name == 'preview_full'
)
;
