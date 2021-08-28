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
  resources = compact([
    one(digitalocean_droplet.legacy_puzzle_massive_volatile[*].urn),
    one(digitalocean_droplet.legacy_puzzle_massive_swap_a[*].urn),
    one(digitalocean_droplet.legacy_puzzle_massive_swap_b[*].urn),
    one(digitalocean_spaces_bucket.cdn[*].urn),
    one(digitalocean_spaces_bucket.cdn_volatile[*].urn),
    digitalocean_spaces_bucket.ephemeral_artifacts.urn,
    digitalocean_spaces_bucket.ephemeral_archive.urn,
    one(digitalocean_droplet.cdn_volatile[*].urn),
    one(digitalocean_droplet.cdn[*].urn),
  ])
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
  tags = [digitalocean_tag.fw_developer_ssh.name]

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
  tags = [digitalocean_tag.fw_web.name]

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
  name   = substr("ephemeral-artifacts-${lower(var.environment)}-${random_uuid.ephemeral_artifacts.result}", 0, 63)
  region = var.bucket_region
  acl    = "private"
  lifecycle_rule {
    enabled = true
    expiration {
      days = 26
    }
  }
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

resource "local_file" "host_inventory" {
  filename        = "${lower(var.environment)}/host_inventory.ansible.cfg"
  file_permission = "0400"
  content         = <<-HOST_INVENTORY
  [all:vars]
  tech_email=${var.tech_email}

  [legacy_puzzle_massive]
  %{for ipv4_address in compact(flatten([digitalocean_droplet.legacy_puzzle_massive_volatile[*].ipv4_address, digitalocean_droplet.legacy_puzzle_massive_swap_a[*].ipv4_address, digitalocean_droplet.legacy_puzzle_massive_swap_b[*].ipv4_address]))~}
  ${ipv4_address}
  %{endfor~}

  [legacy_puzzle_massive:vars]
  new_swap=${var.is_swap_a_active == true && var.is_swap_b_active == false && one(digitalocean_droplet.legacy_puzzle_massive_swap_a[*].ipv4_address) != null ? one(digitalocean_droplet.legacy_puzzle_massive_swap_a[*].ipv4_address) : var.is_swap_a_active == false && var.is_swap_b_active == true && one(digitalocean_droplet.legacy_puzzle_massive_swap_b[*].ipv4_address) != null ? one(digitalocean_droplet.legacy_puzzle_massive_swap_b[*].ipv4_address) : ""}
  old_swap=${var.is_swap_a_active == false && var.is_swap_b_active == true && one(digitalocean_droplet.legacy_puzzle_massive_swap_a[*].ipv4_address) != null ? one(digitalocean_droplet.legacy_puzzle_massive_swap_a[*].ipv4_address) : var.is_swap_a_active == true && var.is_swap_b_active == false && one(digitalocean_droplet.legacy_puzzle_massive_swap_b[*].ipv4_address) != null ? one(digitalocean_droplet.legacy_puzzle_massive_swap_b[*].ipv4_address) : ""}
  ${fileexists("${lower(var.environment)}/puzzle-massive-message.html") ? "message_file=../${lower(var.environment)}/puzzle-massive-message.html" : "message_file=../../root/puzzle-massive-message.html"}
  domain_name=${var.sub_domain}${var.domain}

  [legacy_puzzle_massive_new_swap]
  ${var.is_swap_a_active == true && var.is_swap_b_active == false && one(digitalocean_droplet.legacy_puzzle_massive_swap_a[*].ipv4_address) != null ? one(digitalocean_droplet.legacy_puzzle_massive_swap_a[*].ipv4_address) : var.is_swap_a_active == false && var.is_swap_b_active == true && one(digitalocean_droplet.legacy_puzzle_massive_swap_b[*].ipv4_address) != null ? one(digitalocean_droplet.legacy_puzzle_massive_swap_b[*].ipv4_address) : ""}

  [legacy_puzzle_massive_old_swap]
  ${var.is_swap_a_active == false && var.is_swap_b_active == true && one(digitalocean_droplet.legacy_puzzle_massive_swap_a[*].ipv4_address) != null ? one(digitalocean_droplet.legacy_puzzle_massive_swap_a[*].ipv4_address) : var.is_swap_a_active == true && var.is_swap_b_active == false && one(digitalocean_droplet.legacy_puzzle_massive_swap_b[*].ipv4_address) != null ? one(digitalocean_droplet.legacy_puzzle_massive_swap_b[*].ipv4_address) : ""}

  [cdn]
  %{for ipv4_address in compact(flatten([digitalocean_droplet.cdn_volatile[*].ipv4_address, digitalocean_droplet.cdn[*].ipv4_address]))~}
  ${ipv4_address}
  %{endfor~}

  [cdn:vars]
  domain_name=cdn.${var.sub_domain}${var.domain}
  HOST_INVENTORY
}
