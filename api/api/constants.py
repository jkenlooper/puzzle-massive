POINT_COST_FOR_CHANGING_BIT = 100
NEW_USER_STARTING_POINTS = 1300
# The SKILL_LEVEL_RANGES is also copied in src/gallery/pm-gallery.ts
SKILL_LEVEL_RANGES = set([
    (0,200),
    (200, 600),
    (600, 1600),
    (1600, 2200),
    (2200, 4000),
    (4000, 60000)
])

#status
ACTIVE           = 1   # puzzle is shown on front page if public (points distributed)
IN_QUEUE         = 2   # in the queue of puzzles ready to be assembled (no points) only applies to public
COMPLETED        = 3   # puzzle has been assembled
FROZEN           = 4   # all piece movements are frozen. This can be set by the owner if private. options for a schedule or manaul triggering.
BUGGY_UNLISTED   = 5   # Has issues with piece data
NEEDS_MODERATION = 0   # puzzle image has just been uploaded and has yet to be seen
FAILED_LICENSE   = -1  # image fails to show copyright information
NO_ATTRIBUTION   = -2  # image doesn't show original author
REBUILD          = -3  # puzzle has been placed in rebuild queue
IN_RENDER_QUEUE  = -5  # puzzle image has been accepted and is now in render queue
RENDERING        = -6  # puzzle is currently being rendered
RENDERING_FAILED = -7  # puzzle had error with being rendered
DELETED_LICENSE  = -10 # permission to use image does not comply
DELETED_INAPT    = -11 # inappropiate image for puzzle due to content of image
DELETED_OLD      = -12 # out with the old
DELETED_REQUEST  = -13 # deleted on request from the owner. Can be deleted automatically after completion or date or?
SUGGESTED        = -20 # No image has been set; only a link to source image
SUGGESTED_DONE   = -21 # Suggested image has been processed

#permission
PUBLIC           = 0   # Is listed on the site
PRIVATE          = -1  # Only shows for the owner of the puzzle, can still be played by anyone with the link.

# Puzzle Variant Slug names
CLASSIC = 'classic' # initial_puzzle_variant.sql

# queue levels for puzzles that have IN_QUEUE status
QUEUE_WINNING_BID   = 1  # Player has placed this in front of all other puzzles within skill range (winning bid cost is computed from count of puzzles in bumped)
QUEUE_BUMPED_BID    = 2  # When another puzzle that was the WINNING_BID is bumped out
QUEUE_REBUILD       = 5  # Set when a puzzle is rebuilt by player
QUEUE_NEW           = 6  # Set when a puzzle is created from a new uploaded image
QUEUE_INACTIVE      = 10 # When a puzzle that was ACTIVE gets retired to IN_QUEUE because of old m_date
QUEUE_END_OF_LINE   = 99 # Set when a puzzle is completed. Anything beyond this is also considered end of line and should be sorted by m_date

BID_COST_PER_PUZZLE = 100
