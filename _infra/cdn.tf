locals {
  ephemeral_artifact_keys_cdn = [
    "bin/update-sshd-config.sh",
    "bin/install-latest-stable-nginx.sh",
    "bin/iptables-setup-firewall.sh",
    "snippets/server_name-cdn.nginx.conf",
    "snippets/ssl_certificate-ssl_certificate_key-cdn.nginx.conf",
    "snippets/proxy_pass-cdn.nginx.conf",
    "cdn.nginx.conf",
  ]
}

resource "digitalocean_droplet" "cdn" {
  count      = var.create_cdn ? 1 : 0
  name       = lower("cdn-${var.environment}")
  size       = var.cdn_droplet_size
  resize_disk= false
  image      = "ubuntu-22-04-x64"
  region     = var.region
  vpc_uuid   = digitalocean_vpc.puzzle_massive.id
  ssh_keys   = var.developer_ssh_key_fingerprints
  tags       = [digitalocean_tag.fw_web.name, digitalocean_tag.fw_developer_ssh.name, digitalocean_tag.droplet.name]
  monitoring = true
  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      image,
      user_data,
    ]
  }
  user_data = local_file.cdn_user_data_sh.sensitive_content
}

resource "digitalocean_droplet" "cdn_volatile" {
  count      = var.create_cdn_volatile ? 1 : 0
  name       = lower("cdn-volatile-${var.environment}")
  size       = var.cdn_droplet_size
  image      = "ubuntu-22-04-x64"
  region     = var.region
  vpc_uuid   = digitalocean_vpc.puzzle_massive.id
  ssh_keys   = var.developer_ssh_key_fingerprints
  tags       = [digitalocean_tag.fw_web.name, digitalocean_tag.fw_developer_ssh.name, digitalocean_tag.droplet.name]
  monitoring = true
  lifecycle {
    prevent_destroy = false
    ignore_changes = [
      image,
    ]
  }
  user_data = local_file.cdn_user_data_sh.sensitive_content
}

resource "local_file" "cdn_user_data_sh" {
  filename        = "${lower(var.environment)}/cdn_droplet-user_data.sh"
  file_permission = "0400"
  depends_on = [
    digitalocean_spaces_bucket_object.update_sshd_config_sh,
    digitalocean_spaces_bucket_object.install_latest_stable_nginx_sh,
    digitalocean_spaces_bucket_object.iptables_setup_firewall_sh,
    digitalocean_spaces_bucket_object.nginx_snippets_server_name_cdn_conf[0],
    digitalocean_spaces_bucket_object.nginx_snippets_ssl_certs_cdn_conf[0],
    digitalocean_spaces_bucket_object.nginx_snippets_proxy_pass_cdn_conf[0],
    digitalocean_spaces_bucket_object.cdn_nginx_conf[0],
  ]

  # https://docs.digitalocean.com/products/droplets/how-to/provide-user-data/#retrieve-user-data
  sensitive_content = <<-USER_DATA
    #!/usr/bin/env bash
    set -eu -o pipefail
    set -x

    PASSPHRASE=${random_string.initial_dev_user_password.result}
    ${file("../bin/add-dev-user.sh")}

    ${file("../bin/aws-cli-install.sh")}

    EPHEMERAL_DIR=$(mktemp -d)

    ## One time bucket object grab
    mkdir -p /root/.aws
    cat <<-'AWS_CONFIG' > /root/.aws/config
      [default]
      region =  ${var.bucket_region}
    AWS_CONFIG
    chmod 0600 /root/.aws/config
    cat <<-'AWS_CREDENTIALS' > /root/.aws/credentials
      [default]
      aws_access_key_id = ${var.do_spaces_access_key_id}
      aws_secret_access_key = ${var.do_spaces_secret_access_key}
    AWS_CREDENTIALS
    chmod 0600 /root/.aws/credentials
    %{for key in local.ephemeral_artifact_keys_cdn~}
      aws s3 cp --endpoint=https://${digitalocean_spaces_bucket.ephemeral_artifacts.region}.digitaloceanspaces.com s3://${digitalocean_spaces_bucket.ephemeral_artifacts.name}/${key} $EPHEMERAL_DIR/
    %{endfor~}
    rm -rf /root/.aws

    TMPDIR=$(mktemp -d)
    cd $TMPDIR
    mkdir bin
    mv $EPHEMERAL_DIR/?*.sh bin/
    chmod +x bin/?*.sh

    ./bin/update-sshd-config.sh
    ./bin/install-latest-stable-nginx.sh
    ./bin/iptables-setup-firewall.sh

    mkdir -p /etc/nginx/snippets
    mv $EPHEMERAL_DIR/server_name-cdn.nginx.conf /etc/nginx/snippets/
    mv $EPHEMERAL_DIR/ssl_certificate-ssl_certificate_key-cdn.nginx.conf /etc/nginx/snippets/
    mv $EPHEMERAL_DIR/proxy_pass-cdn.nginx.conf /etc/nginx/snippets/
    mv $EPHEMERAL_DIR/cdn.nginx.conf /etc/nginx/nginx.conf
    cd -
    rm -rf $EPHEMERAL_DIR $TMPDIR

    mkdir -p /var/lib/cdn/cache/
    chown -R nginx:nginx /var/lib/cdn/cache/
    mkdir -p /var/log/nginx/puzzle-massive/
    chown -R nginx:nginx /var/log/nginx/puzzle-massive/

    # TODO: setup service to manage blocked_ip.conf from the admin site.
    touch /etc/nginx/blocked_ip.conf

    nginx -t
    systemctl start nginx
    systemctl reload nginx

    passwd --expire dev
    USER_DATA
}

resource "digitalocean_record" "cdn" {
  count  = var.create_cdn || var.create_cdn_volatile ? 1 : 0
  domain = var.domain
  type   = "A"
  name   = "cdn.${trimsuffix(var.sub_domain, ".")}"
  value  = var.is_cdn_volatile_active ? one(digitalocean_droplet.cdn_volatile[*].ipv4_address) : var.is_cdn_active ? one(digitalocean_droplet.cdn[*].ipv4_address) : null
  # minimum value for TTL on digitalocean DNS is 30 seconds.
  ttl = var.is_volatile_active ? var.volatile_dns_ttl : var.dns_ttl
}

resource "random_uuid" "cdn" {
}

resource "digitalocean_spaces_bucket" "cdn_volatile" {
  count  = var.create_cdn_volatile ? 1 : 0
  name   = substr("puzzle-massive-cdn-${lower(var.environment)}-${random_uuid.cdn.result}", 0, 63)
  region = var.bucket_region
  lifecycle {
    prevent_destroy = false
  }
}
resource "digitalocean_spaces_bucket" "cdn" {
  count  = var.create_cdn ? 1 : 0
  name   = substr("puzzle-massive-cdn-${lower(var.environment)}-${random_uuid.cdn.result}", 0, 63)
  region = var.bucket_region
  lifecycle {
    prevent_destroy = true
  }
}

resource "digitalocean_spaces_bucket_object" "nginx_snippets_server_name_cdn_conf" {
  count   = var.create_cdn || var.create_cdn_volatile ? 1 : 0
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "snippets/server_name-cdn.nginx.conf"
  acl     = "private"
  content = "server_name cdn.${var.sub_domain}${var.domain};"
}

resource "digitalocean_spaces_bucket_object" "nginx_snippets_ssl_certs_cdn_conf" {
  count  = var.create_cdn || var.create_cdn_volatile ? 1 : 0
  region = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key    = "snippets/ssl_certificate-ssl_certificate_key-cdn.nginx.conf"
  acl    = "private"
  # The ssl certs will be uncommented out after certbot has been provisioned and
  # the certs have been created.
  content = <<-CONTENT
  #listen 443 ssl http2;
  #ssl_certificate /etc/letsencrypt/live/cdn.${var.sub_domain}${var.domain}/fullchain.pem;
  #ssl_certificate_key /etc/letsencrypt/live/cdn.${var.sub_domain}${var.domain}/privkey.pem;
  #ssl_certificate /etc/nginx/temporary_fullchain.pem;
  #ssl_certificate_key /etc/nginx/temporary_privkey.pem;
  CONTENT
}

resource "digitalocean_spaces_bucket_object" "nginx_snippets_proxy_pass_cdn_conf" {
  count   = var.create_cdn || var.create_cdn_volatile ? 1 : 0
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "snippets/proxy_pass-cdn.nginx.conf"
  acl     = "private"
  content = "proxy_pass https://${var.create_cdn ? one(digitalocean_spaces_bucket.cdn[*].bucket_domain_name) : one(digitalocean_spaces_bucket.cdn_volatile[*].bucket_domain_name)}/resources/;"



}

resource "digitalocean_spaces_bucket_object" "cdn_nginx_conf" {
  count   = var.create_cdn || var.create_cdn_volatile ? 1 : 0
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "cdn.nginx.conf"
  acl     = "private"
  content = file("../web/cdn.nginx.conf")
}

