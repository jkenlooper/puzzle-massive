select * from Puzzle where status in (:IN_RENDER_QUEUE, :REBUILD) order by queue;
