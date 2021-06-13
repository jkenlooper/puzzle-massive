output "puzzle_massive_ip" {
  description = "IP address of the deployed Puzzle Massive server"
  value = digitalocean_droplet.puzzle_massive.ipv4_address
}
