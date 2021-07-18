output "puzzle_massive_ip_volatile" {
  description = "IP address of the deployed Legacy Puzzle Massive Volatile server"
  value       = one(digitalocean_droplet.legacy_puzzle_massive_volatile[*].ipv4_address)
}
output "puzzle_massive_ip_swap_a" {
  description = "IP address of the deployed Legacy Puzzle Massive Swap A server"
  value       = one(digitalocean_droplet.legacy_puzzle_massive_swap_a[*].ipv4_address)
}
output "puzzle_massive_ip_swap_b" {
  description = "IP address of the deployed Legacy Puzzle Massive Swap B server"
  value       = one(digitalocean_droplet.legacy_puzzle_massive_swap_b[*].ipv4_address)
}
output "cdn" {
  description = "IP address of the deployed CDN server"
  value       = one(digitalocean_droplet.cdn[*].ipv4_address)
}
output "cdn_volatile" {
  description = "IP address of the deployed CDN Volatile server"
  value       = one(digitalocean_droplet.cdn_volatile[*].ipv4_address)
}
output "initial_dev_user_password" {
  description = "Initial password for dev user. This requires changing as soon as the dev user logins."
  value       = random_string.initial_dev_user_password.result
}
