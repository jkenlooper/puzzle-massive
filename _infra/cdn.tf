resource "random_uuid" "cdn_bucket_uuid" {
}

resource "digitalocean_spaces_bucket" "cdn" {
  name   = substr("puzzle-massive-cdn-${lower(var.environment)}-${random_uuid.cdn_bucket_uuid.result}", 0, 63)
  region = var.cdn_bucket_region
}

resource "local_file" "nginx_snippets_server_name_cdn_conf" {
  filename = "${lower(var.environment)}/snippets/server_name-cdn.nginx.conf"
  # Hint that this has been generated from a template and shouldn't be edited by the owner.
  file_permission = "0400"
  content = templatefile("cdn-nginx-snippets-server_name-cdn.nginx.conf.tmpl", {
    DATE            = timestamp()
    CDN_DOMAIN_NAME = "cdn.${var.domain_name}"
  })
}

resource "local_file" "nginx_snippets_proxy_pass_cdn_conf" {
  filename = "${lower(var.environment)}/snippets/proxy_pass-cdn.nginx.conf"
  # Hint that this has been generated from a template and shouldn't be edited by the owner.
  file_permission = "0400"
  sensitive_content = templatefile("cdn-nginx-snippets-proxy_pass-cdn.nginx.conf.tmpl", {
    DATE          = timestamp()
    CDN_PROXY_URL = digitalocean_spaces_bucket.cdn.bucket_domain_name
  })
}
