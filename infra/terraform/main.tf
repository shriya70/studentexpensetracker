provider "docker" {}

resource "docker_image" "app" {
  name = "cloudops-mini-lab:terraform"
  build {
    context    = "${path.module}/../.."
    dockerfile = "Dockerfile"
  }
}

resource "docker_network" "lab" {
  name = "cloudops-terraform-net"
}

resource "docker_container" "app" {
  name  = "cloudops-terraform-app"
  image = docker_image.app.image_id

  env = [
    "APP_VERSION=terraform-local",
    "SERVICE_NAME=cloudops-mini-lab",
  ]

  ports {
    internal = 8000
    external = 8081
  }

  networks_advanced {
    name = docker_network.lab.name
  }

  restart = "unless-stopped"
}
