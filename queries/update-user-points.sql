update User set points = min(:points, :POINTS_CAP) where id = :player_id;
