variable "do_token" {
  description = "DigitalOcean access token.  Keep this secure and use best practices when using these.  It is recommended to export an environment variable for this like TF_VAR_do_token if you aren't entering it manually each time."
  sensitive   = true
}
variable "do_spaces_access_key_id" {
  description = "DigitalOcean Spaces access key ID. Keep this secure and use best practices when using these.  It is recommended to export an environment variable for this like TF_VAR_do_spaces_access_key_id if you aren't entering it manually each time."
  sensitive   = true
}
variable "do_spaces_secret_access_key" {
  description = "DigitalOcean Spaces secret access key. Keep this secure and use best practices when using these.  It is recommended to export an environment variable for this like TF_VAR_do_spaces_secret_access_key if you aren't entering it manually each time."
  sensitive   = true
}
variable "artifacts_bucket_region" {
  description = "Artifacts bucket region"
  default     = "nyc3"
}
variable "artifacts_bucket_name" {
  description = "Artifacts bucket name that will hold versioned distributable gzipped files used for deployments. This bucket should already exist since it is not part of this infrastructure."
}

variable "artifact_dist_tar_gz" {
  description = "The file name of the the created artifact that will be used for deploying to the acceptance or production environments. This artifact is created on the developer's machine via the `make dist` command."
  type        = string
  validation {
    condition     = can(regex("puzzle-massive-.+\\.tar\\.gz", var.artifact_dist_tar_gz))
    error_message = "Must be a file that was generated from the `make dist` command. The Development and Test environments don't use this file when deploying."
  }
}
variable "cdn_bucket_region" {
  description = "CDN bucket region. This will be used for puzzle resources."
  default     = "nyc3"
}

variable "developer_ips" {
  description = "List of ips that will be allowed through the firewall on the SSH port."
  type        = list(string)
}

variable "web_ips" {
  description = "List of ips that will be allowed through the firewall on port 80 and 443."
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}


variable "developer_ssh_key_fingerprints" {
  description = "The fingerprints of any public SSH keys that were added to the DigitalOcean account that should have access to the droplets."
  type        = list(string)
}

variable "environment" {
  description = "Used as part of the name in the project as well as in the hostname of any created droplets."
  default     = "Development"
  validation {
    condition     = can(regex("Development|Test|Acceptance|Production", var.environment))
    error_message = "Must be an environment that has been defined for the Puzzle Massive project."
  }
}
variable "project_environment" {
  description = "Used to set the environment in the DigitalOcean project."
  default     = "Development"
  validation {
    condition     = can(regex("Development|Staging|Production", var.project_environment))
    error_message = "Must be an environment that is acceptable for DigitalOcean projects."
  }
}

variable "legacy_droplet_size" {
  default = "s-2vcpu-4gb"
}

variable "init_user_data_script" {
  type    = string
  default = ""
}

variable "region" {
  default = "nyc1"
}

variable "vpc_ip_range" {
  default = "192.168.126.0/24"
}

variable "project_description" {
  default     = "Massively Multiplayer Jigsaw Puzzle"
  description = "Sets the DigitalOcean project description. Should be set to the current version that is being used."
}

variable "project_version" {
  default     = ""
  description = "Appended to the end of the DigitialOcean project name."
}

variable "checkout_commit" {
  default = "develop"
}
variable "repository_clone_url" {
  description = "Depending on the environment, a git checkout of this repo will occur when deploying."
  default     = "https://github.com/jkenlooper/puzzle-massive.git"
}

variable "dot_env__UNSPLASH_APPLICATION_ID" {
  default     = ""
  description = "Unsplash Application ID. Leave this blank if not using images from Unsplash."
  type        = string
}

variable "dot_env__UNSPLASH_APPLICATION_NAME" {
  default     = ""
  description = "Unsplash Application Name. Leave this blank if not using images from Unsplash."
  type        = string
}

variable "dot_env__UNSPLASH_SECRET" {
  default     = ""
  description = "Unsplash Secret. Leave this blank if not using images from Unsplash."
  type        = string
  sensitive   = true
}

variable "dot_env__SECURE_COOKIE_SECRET" {
  default     = "chocolate chip"
  description = "Some random text for secure cookie. Should be something that is secure and random. This should never change once it has been used for a domain since it would invalidate any cookie that was used to login a player for that site."
  type        = string
  sensitive   = true
}

variable "dot_env__SUGGEST_IMAGE_LINK" {
  default     = "https://any-website-for-uploading/"
  description = "The suggest image link is used on the suggest image for a puzzle page. The player will need to visit this link in order to upload an image for the puzzle that they are suggesting."
  type        = string
}

variable "dot_env__SMTP_HOST" {
  default     = "localhost"
  description = "SMTP Host. Leave blank to disable use of transactional emails."
  type        = string
  sensitive   = true
}

variable "dot_env__SMTP_PORT" {
  default     = "587"
  description = "SMTP Port. Leave blank to disable use of transactional emails."
  type        = string
  sensitive   = true
}

variable "dot_env__SMTP_USER" {
  default     = "user@localhost"
  description = "SMTP User. Leave blank to disable use of transactional emails."
  type        = string
  sensitive   = true
}

variable "dot_env__SMTP_PASSWORD" {
  default     = ""
  description = "SMTP Password. Leave blank to disable use of transactional emails."
  type        = string
  sensitive   = true
}

variable "dot_env__EMAIL_SENDER" {
  default     = "sender@localhost"
  description = "Email Sender. Leave blank to disable use of transactional emails."
  type        = string
}

variable "dot_env__EMAIL_MODERATOR" {
  default     = "moderator@localhost"
  description = "Email Moderator. Leave blank to disable use of transactional emails."
  type        = string
}

variable "dot_env__AUTO_APPROVE_PUZZLES" {
  default     = "y"
  description = "Auto approve uploaded puzzles [y/n]"
  type        = string
  validation {
    condition     = can(regex("y|n", var.dot_env__AUTO_APPROVE_PUZZLES))
    error_message = "Must be either 'y' for yes or 'n' for no."
  }
}

variable "dot_env__LOCAL_PUZZLE_RESOURCES" {
  default     = "y"
  description = "Use local puzzle resource files [y/n]"
  type        = string
  validation {
    condition     = can(regex("y|n", var.dot_env__LOCAL_PUZZLE_RESOURCES))
    error_message = "Must be either 'y' for yes or 'n' for no."
  }
}

variable "dot_env__CDN_BASE_URL" {
  default     = ""
  description = "CDN base URL to use for remote puzzle resources. Leave blank if not using remote puzzle resources."
  type        = string
  validation {
    condition     = can(regex("|https?://.+[^/]", var.dot_env__CDN_BASE_URL))
    error_message = "Should be blank or a valid URL that doesn't end with a '/'."
  }
}

variable "dot_env__PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL" {
  default     = "public, max-age:31536000, immutable"
  description = "CacheControl header that will be used for all objects in the puzzle resources bucket."
  type        = string
}

variable "dot_env__PUZZLE_RULES" {
  default     = "all"
  description = <<-HERE
    Enable rules to prevent players from messing up puzzles for others. These
    rules limit stacking pieces, moving lots of pieces at once, moving pieces to
    the same area, validating the token, etc..
    Set to 'all' to enable all rules
    Leave blank to disable all rules
    Or add only some rules (separate each with a space and no quotes):
    'valid_token' to validate token for piece moves
    'piece_translate_rate' to limit piece move rate per user
    'max_stack_pieces' to limit how many pieces can be stacked
    'stack_pieces' to limit joining pieces when stacked
    'karma_stacked' decrease karma when stacking pieces
    'karma_piece_group_move_max' decrease karma when moving large groups of pieces
    'puzzle_open_rate' to limit how many puzzles can be opened within an hour
    'piece_move_rate' to limit how many pieces can be moved within a minute or so
    'hot_piece' to limit moving the same piece again within a minute or so
    'hot_spot' to limit moving pieces to the same area within 30 seconds
    'too_active' decrease karma on piece move when server responds with 503 error
    'nginx_piece_publish_limit' to use piece move rate limits on nginx web server
    Example of a set of rules to use:
    'valid_token max_stack_pieces stack_pieces karma_stacked karma_piece_group_move_max puzzle_open_rate hot_piece hot_spot'
  HERE
  type        = string
}

variable "dot_env__PUZZLE_FEATURES" {
  default     = "all"
  description = <<-HERE
    Enable puzzle features by listing each here.  See full list by querying the
    database PuzzleFeature table for the 'slug' column.
    Set to 'all' to enable all puzzle features and future ones.
    Leave blank to disable all puzzle features.
    Or add only some puzzle features (separate each with a space and no quotes).
    Example: hidden-preview secret-message
  HERE
  type        = string
}

variable "dot_env__BLOCKEDPLAYER_EXPIRE_TIMEOUTS" {
  default     = "30 300 3600"
  description = <<-HERE
    Timeouts in seconds for each time a player gets blocked on a puzzle. These are
    network specific (IP address) and will reset (expire) on the last item in the
    space separated list. For example, the first time a player gets down to
    0 karma and gets blocked for a puzzle they will need to wait 30 seconds until
    being able to move pieces on that puzzle. The next time a player on that same
    network gets blocked on a puzzle they will need to wait 300 seconds. If no
    players on that network are blocked on a puzzle after the last timeout (3600
    seconds is one hour) the list is reset and the next player that gets blocked
    will again be for 30 seconds.  The last item in this list should always be the
    longest.
  HERE
  type        = string
}

variable "dot_env__MINIMUM_PIECE_COUNT" {
  default     = 20
  description = "Minimum piece count that will be allowed when submitting a puzzle."
  type        = number
}

variable "dot_env__MAXIMUM_PIECE_COUNT" {
  default     = 50000
  description = "Maximum piece count that will be allowed when submitting a puzzle."
  type        = number
}

variable "dot_env__PUZZLE_PIECE_GROUPS" {
  default     = "100 200 400 800 1600 2200 4000 60000"
  description = "Puzzle piece count groupings."
  type        = string
}

variable "dot_env__ACTIVE_PUZZLES_IN_PIECE_GROUPS" {
  default     = "40  20  10  10  5    5    5    5"
  description = "Active puzzles for each puzzle piece count groupings."
  type        = string
}

variable "dot_env__MINIMUM_IN_QUEUE_PUZZLES_IN_PIECE_GROUPS" {
  default     = "6   6   2   2   1    1    0    0"
  description = "Minimum count of puzzles in the queue before the auto rebuild task will randomly add more from the completed puzzles. Grouped by piece counts"
  type        = string
}

variable "dot_env__MAX_POINT_COST_FOR_REBUILDING" {
  default     = 1000
  description = "Max point cost for rebuilding."
  type        = number
}

variable "dot_env__MAX_POINT_COST_FOR_DELETING" {
  default     = 1000
  description = "Max point cost for deleting"
  type        = number
}

variable "dot_env__BID_COST_PER_PUZZLE" {
  default     = 100
  description = "Bid cost per puzzle."
  type        = number
}

variable "dot_env__POINT_COST_FOR_CHANGING_BIT" {
  default     = 100
  description = "Point cost for changing bit."
  type        = number
}

variable "dot_env__POINT_COST_FOR_CHANGING_NAME" {
  default     = 100
  description = "Point cost for changing name."
  type        = number
}

variable "dot_env__NEW_USER_STARTING_POINTS" {
  default     = 1300
  description = "New user starting points."
  type        = number
}

variable "dot_env__POINTS_CAP" {
  default     = 15000
  description = "Points cap."
  type        = number
}

variable "dot_env__BIT_ICON_EXPIRATION" {
  default = [
    "0:    20 minutes",
    "1:    1 day",
    "50:   3 days",
    "400:  7 days",
    "800:  14 days",
    "1600: 1 months"
  ]
  description = "Bit icon expiration extends amounts by player score."
  type        = list(string)
}

variable "dot_env__PUBLISH_WORKER_COUNT" {
  default     = "2"
  description = "The publish worker count is the number of workers that will handle piece movement requests. Set to None to be based on cpu count."
  type        = string
  validation {
    condition     = can(regex("None|\\d+", var.dot_env__PUBLISH_WORKER_COUNT))
    error_message = "Must be either 'None' or a number."
  }
}

variable "dot_env__STREAM_WORKER_COUNT" {
  default     = "2"
  description = "The stream worker count is the number of workers that will handle connections to the stream. Set to None to be based on cpu count."
  type        = string
  validation {
    condition     = can(regex("None|\\d+", var.dot_env__STREAM_WORKER_COUNT))
    error_message = "Must be either 'None' or a number."
  }
}

variable "domain_name" {
  default     = "puzzle.massive.xyz"
  description = "The domain name (FQDN) that will be used for this deployment."
  type        = string
}

variable "dot_env__SITE_TITLE" {
  default     = "Puzzle Massive"
  description = "The site title. This is used in the title of the website as well as in the footer."
  type        = string
}

variable "dot_env__HOME_PAGE_ROUTE" {
  default     = "/chill/site/front/"
  description = <<-HERE
    The home page which loads when visiting the root ('/').
    The NGINX web server will rewrite the URL '/' to this path. This can be
    a different document page defined in chill-data. Or it could be a puzzle page
    that already exists in which case it would be like:
    /chill/site/puzzle/asdf1234/scale/1/
    Use the default (/chill/site/front/) to have it be the most recent puzzle.
  HERE
  type        = string
}

variable "dot_env__SOURCE_CODE_LINK" {
  default     = "https://github.com/jkenlooper/puzzle-massive/"
  description = "Link to the source code used for the custom site.  If you forked the puzzle-massive source code, then change this to be a link to that.  It is required to share the link to your source code to any visitors of your site in order to comply with the GNU Affero General Public License that the puzzle-massive source code is licensed under."
  type        = string
}

variable "dot_env__M3" {
  default     = ""
  description = "M3"
  type        = string
}
