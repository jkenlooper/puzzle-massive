output "puzzle_massive_ip" {
  description = "IP address of the deployed Puzzle Massive server"
  value       = digitalocean_droplet.puzzle_massive.ipv4_address
}
output "initial_dev_user_password" {
  description = "Initial password for dev user. This requires changing as soon as the dev user logins."
  value       = random_string.initial_dev_user_password.result
}
