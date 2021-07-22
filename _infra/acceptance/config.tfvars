# Override these variables for your own setup by creating
# a /_infra/acceptance/private.tfvars file.

environment = "Acceptance"
project_environment = "Staging"

legacy_droplet_size = "s-2vcpu-4gb"
cdn_droplet_size = "s-1vcpu-1gb"

# The default setup for the Acceptance environment is to be volatile.
is_volatile_active = true
create_legacy_puzzle_massive_volatile = true
is_swap_a_active = false
create_legacy_puzzle_massive_swap_a = false
is_swap_b_active = false
create_legacy_puzzle_massive_swap_b = false

is_cdn_volatile_active = true
create_cdn_volatile = true
is_cdn_active = false
create_cdn = false

vpc_ip_range = "192.168.129.0/24"

web_ips = ["0.0.0.0/0", "::/0"]
