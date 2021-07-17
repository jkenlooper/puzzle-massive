locals {
  ephemeral_artifact_keys_cdn = [
    "bin/update-sshd-config.sh",
    "bin/install-latest-stable-nginx.sh",
    "bin/iptables-setup-firewall.sh",
    "snippets/server_name-cdn.nginx.conf",
    "snippets/proxy_pass-cdn.nginx.conf",
    "cdn.nginx.conf",
  ]
}

resource "digitalocean_droplet" "cdn" {
  name     = lower("cdn-${var.environment}")
  size     = var.cdn_droplet_size
  image    = "ubuntu-20-04-x64"
  region   = var.region
  vpc_uuid = digitalocean_vpc.puzzle_massive.id
  ssh_keys = var.developer_ssh_key_fingerprints
  tags     = [digitalocean_tag.fw_web.id, digitalocean_tag.fw_developer_ssh.id]
  depends_on = [
    digitalocean_spaces_bucket_object.update_sshd_config_sh,
    digitalocean_spaces_bucket_object.install_latest_stable_nginx_sh,
    digitalocean_spaces_bucket_object.iptables_setup_firewall_sh,
    digitalocean_spaces_bucket_object.nginx_snippets_server_name_cdn_conf,
    digitalocean_spaces_bucket_object.nginx_snippets_proxy_pass_cdn_conf,
    digitalocean_spaces_bucket_object.cdn_nginx_conf,
  ]
  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      image,
      user_data,
    ]
  }

  # https://docs.digitalocean.com/products/droplets/how-to/provide-user-data/#retrieve-user-data
  user_data = <<-USER_DATA
    #!/usr/bin/env bash
    set -eu -o pipefail
    set -x

    cat <<-'AWS_CREDENTIALS' > aws_credentials
    [default]
    aws_access_key_id = ${var.do_spaces_access_key_id}
    aws_secret_access_key = ${var.do_spaces_secret_access_key}
    AWS_CREDENTIALS

    cat <<-'AWS_CONFIG' > aws_config
    [default]
    region =  ${var.bucket_region}
    AWS_CONFIG

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
    mv $EPHEMERAL_DIR/proxy_pass-cdn.nginx.conf /etc/nginx/snippets/
    mv $EPHEMERAL_DIR/cdn.nginx.conf /etc/nginx/nginx.conf
    cd -
    rm -rf $EPHEMERAL_DIR $TMPDIR

    mkdir -p /var/lib/cdn/cache/
    chown -R nginx:nginx /var/lib/cdn/cache/
    mkdir -p /var/log/nginx/puzzle-massive-cdn/
    chown -R nginx:nginx /var/log/nginx/puzzle-massive-cdn/

    nginx -t
    systemctl start nginx
    systemctl reload nginx

    USER_DATA
}

resource "digitalocean_record" "cdn" {
  domain = var.domain
  type   = "A"
  name   = "cdn.${trimsuffix(var.sub_domain, ".")}"
  value  = digitalocean_droplet.cdn.ipv4_address
}

resource "random_uuid" "cdn" {
}

resource "digitalocean_spaces_bucket" "cdn_volatile" {
  count  = var.create_legacy_puzzle_massive_volatile ? 1 : 0
  name   = substr("puzzle-massive-cdn-${lower(var.environment)}-${random_uuid.cdn.result}", 0, 63)
  region = var.bucket_region
  lifecycle {
    prevent_destroy = false
  }
}
resource "digitalocean_spaces_bucket" "cdn" {
  count  = var.create_legacy_puzzle_massive_swap_a || var.create_legacy_puzzle_massive_swap_b ? 1 : 0
  name   = substr("puzzle-massive-cdn-${lower(var.environment)}-${random_uuid.cdn.result}", 0, 63)
  region = var.bucket_region
  lifecycle {
    prevent_destroy = true
  }
}

resource "digitalocean_spaces_bucket_object" "nginx_snippets_server_name_cdn_conf" {
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "snippets/server_name-cdn.nginx.conf"
  acl     = "private"
  content = "server_name cdn.${var.sub_domain}${var.domain};"
}

resource "digitalocean_spaces_bucket_object" "nginx_snippets_proxy_pass_cdn_conf" {
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "snippets/proxy_pass-cdn.nginx.conf"
  acl     = "private"
  content = "proxy_pass https://${var.create_legacy_puzzle_massive_swap_a || var.create_legacy_puzzle_massive_swap_b ? one(digitalocean_spaces_bucket.cdn[*].bucket_domain_name) : one(digitalocean_spaces_bucket.cdn_volatile[*].bucket_domain_name)}/resources/;"



}

resource "digitalocean_spaces_bucket_object" "cdn_nginx_conf" {
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "cdn.nginx.conf"
  acl     = "private"
  content = file("../web/cdn.nginx.conf")
}

