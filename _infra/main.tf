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
  resources = [
    digitalocean_droplet.puzzle_massive.urn,
    digitalocean_spaces_bucket.cdn.urn,
    digitalocean_spaces_bucket.ephemeral_artifacts.urn,
    digitalocean_spaces_bucket.ephemeral_archive.urn,
    digitalocean_droplet.cdn.urn
  ]
}

# The digitalocean managed certificates are only for load balancers and Spaces CDN.
#resource "digitalocean_certificate" "cert" {
#  name = "puzzle-massive-${lower(var.environment)}"
#  type = "lets_encrypt"
#  domains = [
#    digitalocean_record.cdn.fqdn,
#    digitalocean_record.puzzle_massive.fqdn
#  ]
#}

resource "digitalocean_vpc" "puzzle_massive" {
  name        = "puzzle-massive-${lower(var.environment)}"
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
  name = "puzzle-massive-${lower(var.environment)}-developer-ssh"
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
  name = "puzzle-massive-${lower(var.environment)}-web"
  tags = [digitalocean_tag.fw_web.id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = concat(var.web_ips, var.developer_ips)
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = concat(var.web_ips, var.developer_ips)
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

resource "random_uuid" "ephemeral_artifacts" {
}
resource "digitalocean_spaces_bucket" "ephemeral_artifacts" {
  name   = substr("ephemeral-artifacts-${random_uuid.ephemeral_artifacts.result}", 0, 63)
  region = var.bucket_region
  acl    = "private"
  # These are referenced in user_data, so if they are removed it might make the
  # droplet require to be recreated?
  #lifecycle_rule {
  #  enabled = true
  #  expiration {
  #    days = 26
  #  }
  #}
}

resource "digitalocean_spaces_bucket_object" "update_sshd_config_sh" {
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "bin/update-sshd-config.sh"
  acl     = "private"
  content = file("../bin/update-sshd-config.sh")
}
resource "digitalocean_spaces_bucket_object" "install_latest_stable_nginx_sh" {
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "bin/install-latest-stable-nginx.sh"
  acl     = "private"
  content = file("../bin/install-latest-stable-nginx.sh")
}
resource "digitalocean_spaces_bucket_object" "iptables_setup_firewall_sh" {
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "bin/iptables-setup-firewall.sh"
  acl     = "private"
  content = file("../bin/iptables-setup-firewall.sh")
}
