select * from Puzzle as p
join PuzzleInstance as pi on (p.id = pi.original)
where p.status = :status
and strftime('%s', p.m_date) <= strftime('%s', 'now', '-21 days')
and p.permission = 0 -- public
and p.pieces >= :low and p.pieces < :high
and pi.original == pi.instance
order by random()
limit 5
;
