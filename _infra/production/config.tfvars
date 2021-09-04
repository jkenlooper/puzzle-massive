# Override these variables for your own setup by creating
# a /_infra/production/private.tfvars file.

environment = "Production"
project_environment = "Production"
project_description = ""

legacy_droplet_size = "s-2vcpu-4gb"
cdn_droplet_size = "s-1vcpu-1gb"

# The default setup for the Production environment is to use stateful swaps.
is_volatile_active = false
create_legacy_puzzle_massive_volatile = false
# By default swap_a is created and active. These should be overridden as needed
# by setting them in the /_infra/production/private.tfvars
is_swap_a_active = true
create_legacy_puzzle_massive_swap_a = true
is_swap_b_active = false
create_legacy_puzzle_massive_swap_b = false

# The CDN droplet is not volatile for the Production environment.
is_cdn_volatile_active = false
create_cdn_volatile = false
is_cdn_active = true
create_cdn = true

vpc_ip_range = "192.168.130.0/24"

web_ips = ["0.0.0.0/0", "::/0"]
