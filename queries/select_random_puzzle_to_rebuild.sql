select * from Puzzle
where status = :status
and strftime('%s', m_date) <= strftime('%s', 'now', '-7 days')
order by random()
limit 5
;
