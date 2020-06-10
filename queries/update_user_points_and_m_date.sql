update User set points = min(points + :points, :POINTS_CAP), score = score + :score, m_date = datetime('now') where id = :id
