# Override these variables for your own setup by creating
# a /_infra/test/private.tfvars file.

environment = "Test"
project_environment = "Staging"

# Use the smallest size of droplets in Test.
legacy_droplet_size = "s-1vcpu-1gb"
cdn_droplet_size = "s-1vcpu-1gb"

# The default setup for the Test environment is to be volatile and not
# use a stateful swap for the legacy puzzle massive droplet.
is_volatile_active = true
create_legacy_puzzle_massive_volatile = true
is_swap_a_active = false
create_legacy_puzzle_massive_swap_a = false
is_swap_b_active = false
create_legacy_puzzle_massive_swap_b = false

# The CDN droplet is also volatile for the Test environment.
is_cdn_volatile_active = true
create_cdn_volatile = true
is_cdn_active = false
create_cdn = false

vpc_ip_range = "192.168.128.0/24"

# See notes on this in the _infra/development/config.tfvars
web_ips = ["127.0.0.1"]
