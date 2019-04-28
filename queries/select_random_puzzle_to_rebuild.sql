select * from Puzzle
where status = :status
and strftime('%s', m_date) <= strftime('%s', 'now', '-7 hours')
order by random()
limit 1
;
