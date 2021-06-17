variable "do_token" {
  description = "DigitalOcean access token.  Keep this secure and use best practices when using these.  It is recommended to export an environment variable for this like TF_VAR_do_token if you aren't entering it manually each time."
  sensitive   = true
}
variable "do_spaces_access_key_id" {
  description = "DigitalOcean Spaces access key ID."
  sensitive   = true
}
variable "do_spaces_secret_access_key" {
  description = "DigitalOcean Spaces secret access key"
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

variable "droplet_size" {
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
  default = "https://github.com/jkenlooper/puzzle-massive.git"
}

