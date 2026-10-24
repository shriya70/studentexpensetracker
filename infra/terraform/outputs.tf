output "application_url" {
  description = "Local URL for the Terraform-managed app"
  value       = "http://localhost:8081"
}

output "docker_network_name" {
  value = docker_network.lab.name
}
