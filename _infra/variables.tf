variable "do_token" {
  description = "DigitalOcean token"
  sensitive = true
}

variable "developer_ips" {
  description = "List of ips that will be allowed through the firewall on the SSH port."
  type=list(string)
  default = ["0.0.0.0/0"]
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

variable "droplet_size" {
  default = "s-2vcpu-4gb"
}

variable "region" {
  default = "nyc1"
}

variable "vpc_ip_range" {
  default = "10.0.0.0/24"
}

variable "project_description" {
  default = "Massively Multiplayer Jigsaw Puzzle"
  description = "Sets the DigitalOcean project description. Should be set to the current version that is being used."
}
