# See _infra/variables.tf for description of these.

do_token = ""
do_spaces_access_key_id = ""
do_spaces_secret_access_key = ""

developer_ssh_key_fingerprints = [""]

# Replace the "0.0.0.0/0" with your actual IP address. The "0.0.0.0/0" IP range
# will allow any IP to be allowed through the firewall on the SSH port.
developer_ips = ["0.0.0.0/0"]

region = "nyc1"

# Change this to your fork of the GitHub repository if you have forked the
# project.
repository_clone_url = "https://github.com/jkenlooper/puzzle-massive.git"
