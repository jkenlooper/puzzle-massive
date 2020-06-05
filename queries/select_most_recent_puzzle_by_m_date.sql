select strftime('%s', m_date) as modified from Puzzle
where m_date is not null
order by m_date desc limit 1;
