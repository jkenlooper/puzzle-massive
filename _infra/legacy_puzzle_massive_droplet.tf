resource "digitalocean_droplet" "puzzle_massive" {
  name     = lower("puzzle-massive-${var.environment}")
  size     = var.legacy_droplet_size
  image    = "ubuntu-20-04-x64"
  region   = var.region
  vpc_uuid = digitalocean_vpc.puzzle_massive.id
  ssh_keys = var.developer_ssh_key_fingerprints
  tags     = [digitalocean_tag.fw_web.id, digitalocean_tag.fw_developer_ssh.id]
  depends_on = [
    digitalocean_spaces_bucket_object.add_dev_user_sh,
    digitalocean_spaces_bucket_object.update_sshd_config_sh,
    digitalocean_spaces_bucket_object.set_external_puzzle_massive_in_hosts_sh,
    digitalocean_spaces_bucket_object.install_latest_stable_nginx_sh,
    digitalocean_spaces_bucket_object.setup_sh,
    digitalocean_spaces_bucket_object.iptables_setup_firewall_sh,
    digitalocean_spaces_bucket_object.infra_development_build_sh,
    digitalocean_spaces_bucket_object.infra_acceptance_build_sh,
    digitalocean_spaces_bucket_object.artifact,
  ]

  # https://docs.digitalocean.com/products/droplets/how-to/provide-user-data/#retrieve-user-data
  # Debug via ssh to the droplet and tail the cloud-init logs:
  # tail -f /var/log/cloud-init-output.log
  user_data = <<-USER_DATA
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
      LOCAL_PUZZLE_RESOURCES='${var.dot_env__LOCAL_PUZZLE_RESOURCES}'
      CDN_BASE_URL='${var.dot_env__CDN_BASE_URL}'
      PUZZLE_RESOURCES_BUCKET_REGION='${digitalocean_spaces_bucket.cdn.region}'
      PUZZLE_RESOURCES_BUCKET_ENDPOINT_URL='https://${digitalocean_spaces_bucket.cdn.region}.digitaloceanspaces.com'
      PUZZLE_RESOURCES_BUCKET='${digitalocean_spaces_bucket.cdn.name}'
      PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL='${var.dot_env__PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL}'
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
      DOMAIN_NAME="${var.domain_name}"
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

    cat <<-'HTPASSWD_CONTENT' > .htpasswd
    ${file("${lower(var.environment)}/.htpasswd")}
    HTPASSWD_CONTENT

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

    ${templatefile("one-time-bucket-object-grab.tmpl", {
      bucket_region = digitalocean_spaces_bucket.ephemeral_artifacts.region
      bucket_name   = digitalocean_spaces_bucket.ephemeral_artifacts.name
      keys = [
        "bin/add-dev-user.sh",
        "bin/update-sshd-config.sh",
        "bin/set-external-puzzle-massive-in-hosts.sh",
        "bin/install-latest-stable-nginx.sh",
        "bin/setup.sh",
        "bin/iptables-setup-firewall.sh",
        "bin/infra-development-build.sh",
        "bin/infra-acceptance-build.sh",
        var.artifact
      ]
    })}

    ${file("${lower(var.environment)}/droplet-setup.sh")}
  USER_DATA
}

resource "random_pet" "dot_env__NEW_PUZZLE_CONTRIB" {
  # Changes every month when deploying.
  length = 2
  keepers = {
    month = formatdate("YYYY/MM", timestamp())
  }
}

