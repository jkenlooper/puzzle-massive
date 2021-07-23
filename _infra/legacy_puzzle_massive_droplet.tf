# TODO: Switch to using the digitalocean floating droplet ip instead to avoid
# delays with DNS TTL.
resource "digitalocean_record" "legacy_puzzle_massive" {
  domain = var.domain
  type   = "A"
  name   = trimsuffix(var.sub_domain, ".")
  value  = var.is_floating_ip_active ? one(digitalocean_floating_ip.legacy_puzzle_massive[*].ip_address) : var.is_swap_a_active ? one(digitalocean_droplet.legacy_puzzle_massive_swap_a[*].ipv4_address) : var.is_swap_b_active ? one(digitalocean_droplet.legacy_puzzle_massive_swap_b[*].ipv4_address) : var.is_volatile_active ? one(digitalocean_droplet.legacy_puzzle_massive_volatile[*].ipv4_address) : null
  # minimum value for TTL on digitalocean DNS is 30 seconds.
  ttl    = var.is_volatile_active ? var.volatile_dns_ttl : var.use_short_dns_ttl ? var.short_dns_ttl : var.dns_ttl
}

resource "digitalocean_floating_ip" "legacy_puzzle_massive" {
  count = var.create_floating_ip_puzzle_massive ? 1 : 0
  region = var.region
  droplet_id = var.is_swap_a_active ? one(digitalocean_droplet.legacy_puzzle_massive_swap_a[*].id) : var.is_swap_b_active ? one(digitalocean_droplet.legacy_puzzle_massive_swap_b[*].id) : var.is_volatile_active ? one(digitalocean_droplet.legacy_puzzle_massive_volatile[*].id) : null
}

resource "random_uuid" "ephemeral_archive" {
}
resource "digitalocean_spaces_bucket" "ephemeral_archive" {
  name   = substr("ephemeral-archive-${lower(var.environment)}-${random_uuid.ephemeral_archive.result}", 0, 63)
  region = var.bucket_region
  acl    = "private"
  lifecycle_rule {
    enabled = true
    expiration {
      days = 26
    }
  }
}

resource "digitalocean_spaces_bucket_object" "add_dev_user_sh" {
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "bin/add-dev-user.sh"
  acl     = "private"
  content = file("../bin/add-dev-user.sh")
}
resource "digitalocean_spaces_bucket_object" "set_external_puzzle_massive_in_hosts_sh" {
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "bin/set-external-puzzle-massive-in-hosts.sh"
  acl     = "private"
  content = file("../bin/set-external-puzzle-massive-in-hosts.sh")
}
resource "digitalocean_spaces_bucket_object" "setup_sh" {
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "bin/setup.sh"
  acl     = "private"
  content = file("../bin/setup.sh")
}
resource "digitalocean_spaces_bucket_object" "infra_build__development_sh" {
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "bin/infra-build--development.sh"
  acl     = "private"
  content = file("../bin/infra-build--development.sh")
}
resource "digitalocean_spaces_bucket_object" "infra_build__test_sh" {
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "bin/infra-build--test.sh"
  acl     = "private"
  content = file("../bin/infra-build--test.sh")
}
resource "digitalocean_spaces_bucket_object" "infra_build__acceptance_sh" {
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "bin/infra-build--acceptance.sh"
  acl     = "private"
  content = file("../bin/infra-build--acceptance.sh")
}
resource "digitalocean_spaces_bucket_object" "infra_build__production_sh" {
  region  = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket  = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key     = "bin/infra-build--production.sh"
  acl     = "private"
  content = file("../bin/infra-build--production.sh")
}

resource "digitalocean_spaces_bucket_object" "artifact" {
  region = digitalocean_spaces_bucket.ephemeral_artifacts.region
  bucket = digitalocean_spaces_bucket.ephemeral_artifacts.name
  key    = var.artifact
  acl    = "private"
  source = "${lower(var.environment)}/${var.artifact}"
}

# Ansible will be used to update the droplet after deployment as needed.
resource "digitalocean_droplet" "legacy_puzzle_massive_swap_a" {
  count    = var.create_legacy_puzzle_massive_swap_a ? 1 : 0
  name     = lower("puzzle-massive-${var.environment}-swap-a")
  size     = var.legacy_droplet_size
  image    = "ubuntu-20-04-x64"
  region   = var.region
  vpc_uuid = digitalocean_vpc.puzzle_massive.id
  ssh_keys = var.developer_ssh_key_fingerprints
  tags     = [digitalocean_tag.fw_web.name, digitalocean_tag.fw_developer_ssh.name]
  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      image,
      user_data,
    ]
  }

  # https://docs.digitalocean.com/products/droplets/how-to/provide-user-data/#retrieve-user-data
  # Debug via ssh to the droplet and tail the cloud-init logs:
  # tail -f /var/log/cloud-init-output.log
  # TODO: Should Development and Production be initially provisioned by Ansible?
  #user_data = var.environment == "Test" || var.environment == "Acceptance" ? local_file.legacy_user_data_sh.sensitive_content : "echo 'provision manually'"
  user_data = local_file.legacy_user_data_sh.sensitive_content
}
resource "digitalocean_droplet" "legacy_puzzle_massive_swap_b" {
  count    = var.create_legacy_puzzle_massive_swap_b ? 1 : 0
  name     = lower("puzzle-massive-${var.environment}-swap-b")
  size     = var.legacy_droplet_size
  image    = "ubuntu-20-04-x64"
  region   = var.region
  vpc_uuid = digitalocean_vpc.puzzle_massive.id
  ssh_keys = var.developer_ssh_key_fingerprints
  tags     = [digitalocean_tag.fw_web.name, digitalocean_tag.fw_developer_ssh.name]
  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      # Ansible will be used to update the droplet after deployment as needed.
      image,
      user_data,
    ]
  }

  # https://docs.digitalocean.com/products/droplets/how-to/provide-user-data/#retrieve-user-data
  # Debug via ssh to the droplet and tail the cloud-init logs:
  # tail -f /var/log/cloud-init-output.log
  # TODO: Should Development and Production be initially provisioned by Ansible?
  #user_data = var.environment == "Test" || var.environment == "Acceptance" ? local_file.legacy_user_data_sh.sensitive_content : "echo 'provision manually'"
  user_data = local_file.legacy_user_data_sh.sensitive_content
}

resource "digitalocean_droplet" "legacy_puzzle_massive_volatile" {
  count    = var.create_legacy_puzzle_massive_volatile ? 1 : 0
  name     = lower("puzzle-massive-${var.environment}-volatile")
  size     = var.legacy_droplet_size
  image    = "ubuntu-20-04-x64"
  region   = var.region
  vpc_uuid = digitalocean_vpc.puzzle_massive.id
  ssh_keys = var.developer_ssh_key_fingerprints
  tags     = [digitalocean_tag.fw_web.name, digitalocean_tag.fw_developer_ssh.name]
  lifecycle {
    prevent_destroy = false
    ignore_changes = [
      # Ansible will be used to update the droplet after deployment as needed.
      image,
      user_data,
    ]
  }

  # https://docs.digitalocean.com/products/droplets/how-to/provide-user-data/#retrieve-user-data
  # Debug via ssh to the droplet and tail the cloud-init logs:
  # tail -f /var/log/cloud-init-output.log
  # TODO: Should Development and Production be initially provisioned by Ansible?
  #user_data = var.environment == "Test" || var.environment == "Acceptance" ? local_file.legacy_user_data_sh.sensitive_content : "echo 'provision manually'"
  user_data = local_file.legacy_user_data_sh.sensitive_content
}

resource "random_string" "initial_dev_user_password" {
  length      = 16
  special     = false
  lower       = true
  upper       = true
  number      = true
  min_lower   = 3
  min_upper   = 3
  min_numeric = 3
}

locals {
  ephemeral_artifact_keys = [
    "bin/add-dev-user.sh",
    "bin/update-sshd-config.sh",
    "bin/set-external-puzzle-massive-in-hosts.sh",
    "bin/install-latest-stable-nginx.sh",
    "bin/setup.sh",
    "bin/iptables-setup-firewall.sh",
    "bin/infra-build--development.sh",
    "bin/infra-build--test.sh",
    "bin/infra-build--acceptance.sh",
    "bin/infra-build--production.sh",
    var.artifact
  ]
}

resource "local_file" "legacy_user_data_sh" {
  filename        = "${lower(var.environment)}/legacy_puzzle_massive_droplet-user_data.sh"
  file_permission = "0400"
  depends_on = [
    digitalocean_spaces_bucket_object.add_dev_user_sh,
    digitalocean_spaces_bucket_object.update_sshd_config_sh,
    digitalocean_spaces_bucket_object.set_external_puzzle_massive_in_hosts_sh,
    digitalocean_spaces_bucket_object.install_latest_stable_nginx_sh,
    digitalocean_spaces_bucket_object.setup_sh,
    digitalocean_spaces_bucket_object.iptables_setup_firewall_sh,
    digitalocean_spaces_bucket_object.infra_build__development_sh,
    digitalocean_spaces_bucket_object.infra_build__test_sh,
    digitalocean_spaces_bucket_object.infra_build__acceptance_sh,
    digitalocean_spaces_bucket_object.infra_build__production_sh,
    digitalocean_spaces_bucket_object.artifact,
  ]
  sensitive_content = <<-USER_DATA
    #!/usr/bin/env bash
    set -eu -o pipefail
    set -x
    ARTIFACT=${var.artifact}

    cat <<-'ENV_CONTENT' > .env
      UNSPLASH_APPLICATION_ID='${var.dot_env__UNSPLASH_APPLICATION_ID}'
      UNSPLASH_APPLICATION_NAME='${var.dot_env__UNSPLASH_APPLICATION_NAME}'
      UNSPLASH_SECRET='${var.dot_env__UNSPLASH_SECRET}'
      NEW_PUZZLE_CONTRIB='${var.dot_env__NEW_PUZZLE_CONTRIB}'
      SECURE_COOKIE_SECRET='${var.dot_env__SECURE_COOKIE_SECRET}'
      SUGGEST_IMAGE_LINK='${var.dot_env__SUGGEST_IMAGE_LINK}'
      SMTP_HOST='${var.dot_env__SMTP_HOST}'
      SMTP_PORT='${var.dot_env__SMTP_PORT}'
      SMTP_USER='${var.dot_env__SMTP_USER}'
      SMTP_PASSWORD='${var.dot_env__SMTP_PASSWORD}'
      EMAIL_SENDER='${var.dot_env__EMAIL_SENDER}'
      EMAIL_MODERATOR='${var.dot_env__EMAIL_MODERATOR}'
      AUTO_APPROVE_PUZZLES='${var.dot_env__AUTO_APPROVE_PUZZLES}'
      LOCAL_PUZZLE_RESOURCES='${var.create_cdn || var.create_cdn_volatile ? var.dot_env__LOCAL_PUZZLE_RESOURCES : "y"}'
      CDN_BASE_URL='${var.create_cdn || var.create_cdn_volatile ? "http://${one(digitalocean_record.cdn[*].fqdn)}" : ""}'
      PUZZLE_RESOURCES_BUCKET_REGION='${var.create_cdn ? one(digitalocean_spaces_bucket.cdn[*].region) : var.create_cdn_volatile ? one(digitalocean_spaces_bucket.cdn_volatile[*].region) : ""}'
      PUZZLE_RESOURCES_BUCKET_ENDPOINT_URL='${var.create_cdn || var.create_cdn_volatile ? "https://${var.create_cdn ? one(digitalocean_spaces_bucket.cdn[*].region) : one(digitalocean_spaces_bucket.cdn_volatile[*].region)}.digitaloceanspaces.com" : ""}'
      PUZZLE_RESOURCES_BUCKET='${var.create_cdn ? one(digitalocean_spaces_bucket.cdn[*].name) : var.create_cdn_volatile ? one(digitalocean_spaces_bucket.cdn_volatile[*].name) : ""}'
      PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL='${var.dot_env__PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL}'
      EPHEMERAL_ARCHIVE_ENDPOINT_URL='https://${digitalocean_spaces_bucket.ephemeral_archive.region}.digitaloceanspaces.com'
      EPHEMERAL_ARCHIVE_BUCKET='${digitalocean_spaces_bucket.ephemeral_archive.name}'
      PUZZLE_RULES="${var.dot_env__PUZZLE_RULES}"
      PUZZLE_FEATURES="${var.dot_env__PUZZLE_FEATURES}"
      BLOCKEDPLAYER_EXPIRE_TIMEOUTS="${var.dot_env__BLOCKEDPLAYER_EXPIRE_TIMEOUTS}"
      MINIMUM_PIECE_COUNT=${var.dot_env__MINIMUM_PIECE_COUNT}
      MAXIMUM_PIECE_COUNT=${var.dot_env__MAXIMUM_PIECE_COUNT}
      PUZZLE_PIECE_GROUPS="${var.dot_env__PUZZLE_PIECE_GROUPS}"
      ACTIVE_PUZZLES_IN_PIECE_GROUPS="${var.dot_env__ACTIVE_PUZZLES_IN_PIECE_GROUPS}"
      MINIMUM_IN_QUEUE_PUZZLES_IN_PIECE_GROUPS="${var.dot_env__MINIMUM_IN_QUEUE_PUZZLES_IN_PIECE_GROUPS}"
      MAX_POINT_COST_FOR_REBUILDING=${var.dot_env__MAX_POINT_COST_FOR_REBUILDING}
      MAX_POINT_COST_FOR_DELETING=${var.dot_env__MAX_POINT_COST_FOR_DELETING}
      BID_COST_PER_PUZZLE=${var.dot_env__BID_COST_PER_PUZZLE}
      POINT_COST_FOR_CHANGING_BIT=${var.dot_env__POINT_COST_FOR_CHANGING_BIT}
      POINT_COST_FOR_CHANGING_NAME=${var.dot_env__POINT_COST_FOR_CHANGING_NAME}
      NEW_USER_STARTING_POINTS=${var.dot_env__NEW_USER_STARTING_POINTS}
      POINTS_CAP=${var.dot_env__POINTS_CAP}
      BIT_ICON_EXPIRATION="${join(",\n", var.dot_env__BIT_ICON_EXPIRATION)}"
      PUBLISH_WORKER_COUNT=${var.dot_env__PUBLISH_WORKER_COUNT}
      STREAM_WORKER_COUNT=${var.dot_env__STREAM_WORKER_COUNT}
      DOMAIN_NAME="${var.sub_domain}${var.domain}"
      SITE_TITLE="${var.dot_env__SITE_TITLE}"
      HOME_PAGE_ROUTE="${var.dot_env__HOME_PAGE_ROUTE}"
      SOURCE_CODE_LINK="${var.dot_env__SOURCE_CODE_LINK}"
      M3="${var.dot_env__M3}"
      HOSTCHILL="127.0.0.1"
      HOSTCACHE="127.0.0.1"
      HOSTORIGIN="127.0.0.1"
      HOSTAPI="127.0.0.1"
      HOSTPUBLISH="127.0.0.1"
      HOSTDIVULGER="127.0.0.1"
      HOSTSTREAM="127.0.0.1"
      HOSTREDIS="127.0.0.1"
    ENV_CONTENT

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
    %{for key in local.ephemeral_artifact_keys~}
      aws s3 cp --endpoint=https://${digitalocean_spaces_bucket.ephemeral_artifacts.region}.digitaloceanspaces.com s3://${digitalocean_spaces_bucket.ephemeral_artifacts.name}/${key} $EPHEMERAL_DIR/
    %{endfor~}
    rm -rf /root/.aws

    pwd_dir=$PWD
    TMPDIR=$(mktemp -d)
    mv .env $TMPDIR/
    cd $TMPDIR
    mkdir bin
    mv $EPHEMERAL_DIR/?*.sh bin/
    chmod +x bin/?*.sh

    ./bin/add-dev-user.sh ${random_string.initial_dev_user_password.result}
    ./bin/update-sshd-config.sh
    ./bin/set-external-puzzle-massive-in-hosts.sh
    ./bin/install-latest-stable-nginx.sh
    ./bin/setup.sh
    ./bin/iptables-setup-firewall.sh

    mkdir -p /home/dev/.aws
    cat <<-'AWS_CREDENTIALS_APP' > /home/dev/.aws/credentials
      [default]
      aws_access_key_id = ${var.do_app_spaces_access_key_id}
      aws_secret_access_key = ${var.do_app_spaces_secret_access_key}
    AWS_CREDENTIALS_APP
    chmod 0600 /home/dev/.aws/credentials
    cat <<-'AWS_CONFIG_APP' > /home/dev/.aws/config
      [default]
      region =  ${var.bucket_region}
    AWS_CONFIG_APP
    chmod 0600 /home/dev/.aws/config
    chown -R dev:dev /home/dev/.aws

    mv $EPHEMERAL_DIR/$ARTIFACT /home/dev/

    ./bin/infra-build--${lower(var.environment)}.sh $ARTIFACT $(realpath .env)
    cd -
    rm -rf $EPHEMERAL_DIR $TMPDIR
    passwd --expire dev
  USER_DATA
}
