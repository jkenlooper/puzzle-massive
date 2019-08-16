select u.points from User as u
join Puzzle as pz
join PuzzleInstance as pi on (pi.instance = pz.id)
where u.id = :user
-- no point cost for puzzle instances owned by the player
and (u.points >= :pieces or (pi.original != pi.instance and pz.owner == :user))
and pz.id = :puzzle
and (pi.original == pi.instance or pz.owner == :user);
