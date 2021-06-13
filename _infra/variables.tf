variable "do_token" {
  description = "DigitalOcean access token.  Keep this secure and use best practices when using these.  It is recommended to export an environment variable for this like TF_VAR_do_token if you aren't entering it manually each time."
  sensitive = true
}

variable "developer_ips" {
  description = "List of ips that will be allowed through the firewall on the SSH port."
  type=list(string)
}

variable "web_ips" {
  description = "List of ips that will be allowed through the firewall on port 80 and 443."
  type=list(string)
  default=["0.0.0.0/0", "::/0"]
}


variable "developer_ssh_key_fingerprints" {
  description = "The fingerprints of any public SSH keys that were added to the DigitalOcean account that should have access to the droplets."
  type=list(string)
}

variable "environment" {
  description = "Used as part of the name in the project as well as in the hostname of any created droplets."
  default = "Development"
  validation {
    condition = can(regex("Development|Test|Acceptance|Production", var.environment))
    error_message = "Must be an environment that has been defined for the Puzzle Massive project."
  }
}
variable "project_environment" {
  description = "Used to set the environment in the DigitalOcean project."
  default = "Development"
  validation {
    condition = can(regex("Development|Staging|Production", var.project_environment))
    error_message = "Must be an environment that is acceptable for DigitalOcean projects."
  }
}

variable "droplet_size" {
  default = "s-2vcpu-4gb"
}

variable "init_user_data_script" {
  type=string
  default = ""
}

variable "region" {
  default = "nyc1"
}

variable "vpc_ip_range" {
  default = "192.168.126.0/24"
}

variable "project_description" {
  default = "Massively Multiplayer Jigsaw Puzzle"
  description = "Sets the DigitalOcean project description. Should be set to the current version that is being used."
}

variable "project_version" {
  default = ""
  description = "Appended to the end of the DigitialOcean project name.  Allows multiple versions of that environment to be deployed. Can also be left blank for Production in-place deployments."
}

variable "checkout_commit" {
  default = "develop"
}
variable "repository_clone_url" {
  description = "Depending on the environment, a git checkout of this repo will occur when deploying."
  default = "https://github.com/jkenlooper/puzzle-massive.git"
}

