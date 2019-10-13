update Puzzle set queue = 1, -- QUEUE_WINNING_BID
m_date = datetime('now')
where status = 2 -- IN_QUEUE
and id = :puzzle
;
