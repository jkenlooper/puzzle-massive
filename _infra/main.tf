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
  name     = "puzzle-massive-${var.environment}"
  description = "Puzzle Massive network for the ${var.environment} environment"
  region   = var.region
}

resource "digitalocean_droplet" "puzzle_massive" {
  name     = lower("puzzle-massive-${var.environment}")
  size     = var.droplet_size
  image    = "ubuntu-20-04-x64"
  region   = var.region
  vpc_uuid = digitalocean_vpc.puzzle_massive.id
  ssh_keys = var.developer_ssh_key_fingerprints
  tags     = [digitalocean_tag.fw_puzzle_massive.id]

  user_data = join("\n", concat([
    "#!/usr/bin/env bash",
    "CHECKOUT_COMMIT=${var.checkout_commit}",
    "REPOSITORY_CLONE_URL=${var.repository_clone_url}",

    "cat <<-'ENV_CONTENT' > .env",
    file("${lower(var.environment)}/.env"),
    "ENV_CONTENT",

    "cat <<-'HTPASSWD_CONTENT' > .htpasswd",
    file("${lower(var.environment)}/.htpasswd"),
    "HTPASSWD_CONTENT",

    file("${lower(var.environment)}/droplet-setup.sh")
  ]))
}

resource "digitalocean_tag" "fw_puzzle_massive" {
  name = "fw_puzzle_massive"
}

resource "digitalocean_firewall" "puzzle_massive" {
  name = "puzzle-massive"
  tags = [digitalocean_tag.fw_puzzle_massive.id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = var.developer_ips
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "icmp"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range       = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range       = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}
