select * from Puzzle
where status = :status
and strftime('%s', m_date) <= strftime('%s', 'now', '-21 days')
and permission = 0 -- public
order by random()
limit 5
;
