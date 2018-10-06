
#status
ACTIVE           = 1   # puzzle is shown on front page if public (points distributed)
IN_QUEUE         = 2   # in the queue of puzzles ready to be assembled (no points) only applies to public
COMPLETED        = 3   # puzzle has been assembled
FROZEN           = 4   # all piece movements are frozen. This can be set by the owner if private. options for a schedule or manaul triggering.
BUGGY_UNLISTED   = 5   # Has issues with piece data
NEEDS_MODERATION = 0   # puzzle image has just been uploaded and has yet to be seen
FAILED_LICENSE   = -1  # image fails to show copyright information
NO_ATTRIBUTION   = -2  # image doesn't show original author
IN_RENDER_QUEUE  = -5  # puzzle image has been accepted and is now in render queue
RENDERING        = -6  # puzzle is currently being rendered
RENDERING_FAILED = -7  # puzzle had error with being rendered
DELETED_LICENSE  = -10 # permission to use image does not comply
DELETED_INAPT    = -11 # inappropiate image for puzzle due to content of image
DELETED_OLD      = -12 # out with the old
DELETED_REQUEST  = -13 # deleted on request from the owner. Can be deleted automatically after completion or date or?
SUGGESTED        = -20 # No image has been set; only a link to source image
