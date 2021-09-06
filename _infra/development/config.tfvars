# Override these variables for your own setup by creating
# a /_infra/development/private.tfvars file.

environment = "Development"
project_environment = "Development"

# Use the smallest size of droplets in Development.
legacy_droplet_size = "s-1vcpu-1gb"
cdn_droplet_size = "s-1vcpu-1gb"

# The default setup for the Development environment is to be volatile and not
# use a stateful swap for the legacy puzzle massive droplet.
is_volatile_active = true
create_legacy_puzzle_massive_volatile = true
is_swap_a_active = false
create_legacy_puzzle_massive_swap_a = false
is_swap_b_active = false
create_legacy_puzzle_massive_swap_b = false

# The CDN droplet is also volatile for the Development environment.
is_cdn_volatile_active = true
create_cdn_volatile = true
is_cdn_active = false
create_cdn = false

vpc_ip_range = "192.168.127.0/24"

# The Development environment blocks all public access by default. Note that the
# developer_ips and admin_ips are allowed through the firewall.
web_ips = ["127.0.0.1"]
