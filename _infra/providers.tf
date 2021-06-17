# Configure the DigitalOcean Provider
provider "digitalocean" {
  # https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs#argument-reference
  # It is recommended to set the DigitalOcean Access Token and Spaces Access Keys
  # via environment variables and export them.
  # TF_VAR_do_token
  # TF_VAR_do_spaces_access_key_id
  # TF_VAR_do_spaces_secret_access_key
  token             = var.do_token
  spaces_access_id  = var.do_spaces_access_key_id
  spaces_secret_key = var.do_spaces_secret_access_key
}
