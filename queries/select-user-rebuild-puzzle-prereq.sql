select u.points from User as u
join Puzzle as pz on (u.points >= :pieces)
join PuzzleInstance as pi on (pi.instance = pz.id)
where u.id = :user
and pz.id = :puzzle
and (pi.original == pi.instance or pz.owner == :user);
