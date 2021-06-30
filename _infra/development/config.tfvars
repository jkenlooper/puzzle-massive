environment = "Development"
project_environment = "Development"
project_description = ""
project_version = ""
checkout_commit = "feature/infra"

legacy_droplet_size = "s-1vcpu-1gb"

vpc_ip_range = "192.168.127.0/24"

# Requires using a SOCKS proxy in order to view.
# Assuming that their is an entry for local-puzzle-massive that points to your
# digitalocean droplet in /etc/hosts
# ssh -D 7171 dev@local-puzzle-massive
# Then setup your SOCKS v5 host to be localhost and 7171 port
# Recommended to use FireFox web browser to set socks proxy instead of setting
# your whole system.
web_ips = ["127.0.0.1"]
