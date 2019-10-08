update Puzzle set status = 2, -- IN_QUEUE
queue = 10 -- QUEUE_INACTIVE
where status = 1 -- ACTIVE
and strftime('%s', m_date) < strftime('%s', 'now', '-7 days');
