# See _infra/variables.tf for description of these.
#
# Copy this file and rename it to _infra/private.auto.tfvars
#
# Do not share the renamed file as it may contain sensitive content like
# passwords and access keys. Can also set these variables via environment
# variables if they are prepended with 'TF_VAR_'. See Terraform documentation.

# Recommended to set these do_* variables as environment variables and not store
# them unencrypted on the file system. The file 'secure_tfvars.sh' below will
# prompt for each and store it that way until you exit the terminal. Use the
# 'source' command like this when in the _infra directory:
# source secure_tfvars.sh
#
# Alternately, the command to encrypt these access keys to disk can be used:
# source encrypt_tfvars.sh development
#
# They can then be decrypted and set via the command:
# source decrypt_tfvars.sh development
#
##do_token                    = ""
##do_spaces_access_key_id     = ""
##do_spaces_secret_access_key = ""

# Get the ssh key fingerprints from your DigitalOcean account
#developer_ssh_key_fingerprints = [""]

# Replace the "0.0.0.0/0" with your actual IP address. The "0.0.0.0/0" IP range
# will allow any IP to be allowed through the firewall on the SSH port.
#developer_ips = ["0.0.0.0/0"]

#region = "nyc1"
#bucket_region = "nyc3"


#admin_password = ""

#dot_env__UNSPLASH_APPLICATION_ID   = ""
#dot_env__UNSPLASH_APPLICATION_NAME = ""
#dot_env__UNSPLASH_SECRET           = ""

#dot_env__SUGGEST_IMAGE_LINK = ""
#dot_env__CLIENT_MAX_BODY_SIZE__PUZZLE_UPLOAD = "10m"
#dot_env__CLIENT_MAX_BODY_SIZE__ADMIN_PUZZLE_PROMOTE_SUGGESTED = "100m"

#dot_env__SMTP_HOST       = ""
#dot_env__SMTP_PORT       = ""
#dot_env__SMTP_USER       = ""
#dot_env__SMTP_PASSWORD   = ""
#dot_env__EMAIL_SENDER    = ""
#dot_env__EMAIL_MODERATOR = ""

#dot_env__PUZZLE_RULES = ""

#dot_env__PUZZLE_FEATURES = ""

#dot_env__BLOCKEDPLAYER_EXPIRE_TIMEOUTS            = "10 30 300 600 1200 2400 3600"
#dot_env__MINIMUM_IN_QUEUE_PUZZLES_IN_PIECE_GROUPS = "6   6   2   2   1    1    1    1"
#dot_env__MAX_POINT_COST_FOR_DELETING              = 500
#dot_env__BID_COST_PER_PUZZLE                      = 10
#dot_env__POINT_COST_FOR_CHANGING_BIT              = 10
#dot_env__POINT_COST_FOR_CHANGING_NAME             = 10
#dot_env__BIT_ICON_EXPIRATION = [
#  "0:    2 days",
#  "1:    4 days",
#  "50:   14 days",
#  "400:  1 months",
#  "800:  4 months",
#  "1600: 8 months"
#]
