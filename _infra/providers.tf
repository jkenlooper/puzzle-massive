# Configure the DigitalOcean Provider
provider "digitalocean" {
  # https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs#argument-reference
  token = var.do_token
}


