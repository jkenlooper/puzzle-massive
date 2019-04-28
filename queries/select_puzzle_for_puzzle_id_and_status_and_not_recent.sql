select * from Puzzle where puzzle_id = :puzzle_id and status = :status
and strftime('%s', m_date) <= strftime('%s', 'now', '-7 hours');
