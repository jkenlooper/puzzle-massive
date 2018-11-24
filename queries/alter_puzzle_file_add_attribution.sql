alter table PuzzleFile add
    attribution integer references Attribution (id)
    ;
