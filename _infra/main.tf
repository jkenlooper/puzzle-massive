# TODO: split this out into multiple .tf files

terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

resource "digitalocean_project" "puzzle_massive" {
  name        = "Puzzle Massive - ${var.environment} ${var.project_version}"
  description = var.project_description
  purpose     = "Web Application"
  environment = var.project_environment
  resources   = [digitalocean_droplet.puzzle_massive.urn]
}

resource "digitalocean_vpc" "puzzle_massive" {
  name        = "puzzle-massive-${var.environment}"
  description = "Puzzle Massive network for the ${var.environment} environment"
  region      = var.region
  ip_range    = var.vpc_ip_range
}

resource "digitalocean_tag" "fw_developer_ssh" {
  name = "fw_puzzle_massive_${lower(var.environment)}_developer_ssh"
}
resource "digitalocean_tag" "fw_web" {
  name = "fw_puzzle_massive_${lower(var.environment)}_web"
}

resource "digitalocean_firewall" "developer_ssh" {
  name = "puzzle-massive-developer-ssh"
  tags = [digitalocean_tag.fw_developer_ssh.id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = var.developer_ips
  }
  outbound_rule {
    protocol              = "tcp"
    port_range            = "22"
    destination_addresses = var.developer_ips
  }
}

resource "digitalocean_firewall" "web" {
  name = "puzzle-massive-web"
  tags = [digitalocean_tag.fw_web.id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = var.web_ips
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = var.web_ips
  }

  inbound_rule {
    protocol         = "icmp"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

resource "digitalocean_spaces_bucket_object" "puzzle_massive_dist_tar" {
  region = var.artifacts_bucket_region
  bucket = var.artifacts_bucket_name
  key    = "puzzle-massive/${lower(var.environment)}/${var.artifact_dist_tar_gz}"
  acl    = "private"
  source = "${lower(var.environment)}/${var.artifact_dist_tar_gz}"
}

resource "local_file" "aws_credentials" {
  filename = "${lower(var.environment)}/aws_credentials"
  # Hint that this has been generated from a template and shouldn't be edited by the owner.
  file_permission = "0400"
  sensitive_content = templatefile("aws_credentials.tmpl", {
    do_spaces_access_key_id     = var.do_spaces_access_key_id
    do_spaces_secret_access_key = var.do_spaces_secret_access_key
  })
}

resource "local_file" "aws_config" {
  filename = "${lower(var.environment)}/aws_config"
  # Hint that this has been generated from a template and shouldn't be edited by the owner.
  file_permission = "0400"
  content = templatefile("aws_config.tmpl", {
    artifacts_bucket_region = var.artifacts_bucket_region
  })
}
