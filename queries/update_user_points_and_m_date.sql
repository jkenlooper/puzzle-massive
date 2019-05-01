-- TODO: move score out of this and into redis to improve the player-ranks
update User set points = min(points + :points, :POINTS_CAP), score = score + :score, m_date = datetime('now') where id = :id
