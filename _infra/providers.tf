# Configure the DigitalOcean Provider
provider "digitalocean" {
  # https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs#argument-reference
  token = var.do_token
  # It is a better practice to set the DigitalOcean Access Token via the
  # environment variable DIGITALOCEAN_ACCESS_TOKEN
}
