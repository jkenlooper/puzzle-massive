redis for tracking piece movements
sortedset blockedplayers ip-user timestamp

##Puzzle karma (0-50) is shown to player.

Moving a piece will lower karma with the amount depending on puzzle size. When
karma is at 0; start deducting points until points are also at 0. Prevent any
further piece movements when both karma for a puzzle and player points are 0.

Start with 10 and earn more by joining pieces.
Lose them by moving grouped pieces, stacking pieces, moving a piece that was
recently moved.

string karma:{puzzle}:{ip} 50

- Script that moves random pieces.
- New players that move lots of pieces with no joining.
- Player that moves grouped pieces around too much.
- Player that moves a piece that some other player just moved.
- Script that watches for piece movements and moves a recently moved piece somewhere else.

## Hot spots

Track hot spots per user.

string hotspot:{puzzle}:{user}:{x}:{y}

- Script that moves random pieces to a single spot and then moves that piece elsewhere.
- Player that quickly moves the same piece to the same location. Tapping.
- Player or script that moves pieces quickly to stack them.

Track hot pieces per user. Limit depends on puzzle size.

- Player that moves the same piece to a different location multiple times.

string hotpc:{puzzle}:{user}:{piece} [number of moves]

## Move rate on puzzle per user

Track piece movement rate on a puzzle per user (global move rate per ip is
handled by nginx). The timestamp is rounded to the minute. Decrement the karma
when this is above the threshold.

string pcrate:{puzzle}:{user}:{timestamp} [number of moves]

## Puzzle jumping

Track how many different puzzles that the player has moved pieces on recently.
Timestamp rounded to the day. Set initial puzzle karma to 0 when over
threshold. Shouldn't impact normal players that are joining pieces as they
will have points to compensate. Increment by the piece count of each puzzle opened.

set pzrate:{user}:{today} [puzzle]

- Script that cycles through all puzzles and moves only a few pieces on each.
