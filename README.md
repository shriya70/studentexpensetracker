# CloudOps Mini Lab — Cloud-Native Service with CI/CD, IaC, Containers and Observability

A small, practical lab project that demonstrates the core parts of a DevOps/cloud-computing workflow. It runs locally, so you do not need a paid cloud account.

## What you will build

A status dashboard served by a Python/Flask web app. The service exposes health and readiness probes, a JSON status API, Prometheus metrics, and structured JSON logs. Docker Compose runs the app with Prometheus and Grafana; Kubernetes manifests demonstrate multiple replicas, rolling updates, health probes and autoscaling; Terraform demonstrates Infrastructure as Code against the local Docker Engine; GitHub Actions runs tests and publishes a container image to GitHub Container Registry (GHCR) after a successful push to `main`.

| Learning outcome | Included in this repository |
|---|---|
| Version control strategies | Git setup, feature-branch workflow, small commits, tags and rollback notes below |
| CI/CD automation | `.github/workflows/ci-cd.yml`: pytest on pull requests/pushes; build and publish image to GHCR on `main` |
| Infrastructure as Code | `infra/terraform/`: Docker image, network and container described as Terraform resources |
| Container CLI | Build/run/inspect/logs/exec/stats/stop/remove exercises below |
| Container orchestration | `docker-compose.yml` for local multi-service orchestration; `k8s/` for Kubernetes replicas, service routing, rolling updates, probes and HPA |
| Observability | Prometheus metrics, provisioned Grafana dashboard and JSON logs on stdout |
| VirtualBox | Suggested Ubuntu VM lab setup below; Docker runs inside the VM and the same commands apply |

> **Scope note:** This is a student lab, not a hardened production service. The app has no database and exposes demo status, not actual cloud infrastructure status. Grafana uses a simple lab password. Do not expose the lab ports to an untrusted network.

## Architecture

```text
Browser :8080
    |
    v
Docker Compose network ----------------------+
    |                                        |
    v                                        v
Flask/Gunicorn app :8000                 Prometheus :9090
    |  /health, /ready, /api/status          | scrapes /metrics
    |  /metrics + JSON stdout logs            v
    +------------------------------------> Grafana :3000

Optional paths:
  Terraform -> local Docker Engine -> standalone app on host port 8081
  Kubernetes -> Deployment (2 pods) -> Service (NodePort 30080) -> app pods
  GitHub Actions -> tests -> container build/publish to GHCR on main
```

## Prerequisites

- Git
- Docker Engine and Docker Compose v2 (`docker compose`)
- Python 3.10+ if you want to run tests on your host
- Optional: Oracle VirtualBox and an Ubuntu LTS VM; Terraform; Minikube for Kubernetes

Commands below are intended for a terminal inside Ubuntu/Linux or Windows PowerShell with Docker configured. In a VirtualBox VM, run them in the **Ubuntu guest** terminal.

## 1. Run the full app + monitoring stack

```bash
git clone <your-repository-url>
cd cloudops-mini-lab
docker compose up --build -d
```

Open these URLs from the machine running Docker:

- App dashboard: <http://localhost:8080>
- Health endpoint: <http://localhost:8080/health>
- Readiness endpoint: <http://localhost:8080/ready>
- JSON status: <http://localhost:8080/api/status>
- Prometheus metrics: <http://localhost:8080/metrics>
- Prometheus UI: <http://localhost:9090>
- Grafana: <http://localhost:3000> (username `admin`, password `cloudops123`)

In Grafana, open **Dashboards → CloudOps Lab → CloudOps Mini Lab Overview**. The dashboard shows request rate, p95 latency and rates grouped by HTTP status. Visit the app or refresh endpoints a few times to generate metrics; allow a few seconds for Prometheus to scrape them.

Verify the service and metrics:

```bash
./scripts/smoke-test.sh
# Or pass a different base URL:
./scripts/smoke-test.sh http://127.0.0.1:8080
```

Useful day-to-day commands:

```bash
docker compose ps
docker compose logs -f app
docker compose logs --tail=100 prometheus
docker compose restart app
docker compose down             # stop/remove containers and network
docker compose down -v          # also delete Prometheus/Grafana data volumes
```

## 2. Docker CLI lab exercises

Run these after completing step 1. The Compose app already built the `cloudops-mini-lab:local` image.

```bash
# List images and running containers
docker image ls
docker ps

# Inspect settings, network addresses and published ports
docker inspect cloudops-app
docker port cloudops-app
docker network inspect cloudops-observability

# Read the app's stdout logs (JSON request events are written here)
docker logs --tail 30 cloudops-app
docker logs -f cloudops-app

# Open a shell in the running container (the image is intentionally minimal)
docker exec -it cloudops-app sh
# Exit the container shell with: exit

# Sample CPU/memory/network I/O statistics
docker stats cloudops-app

# Test the health endpoint from inside the container
docker exec cloudops-app python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read().decode())"

# Stop/start the service container
docker stop cloudops-app
docker start cloudops-app

# Rebuild only the app after modifying app.py
docker compose up --build -d app
```

**Learning check:** explain the difference between an image and a container; identify the host port versus container port; find a request event in `docker logs`; and describe why containers should not be treated as the durable storage location for important data.

## 3. VirtualBox + Ubuntu lab (recommended for a cloud-computing practical)

This isolates the Linux/Docker lab from your host operating system.

1. Install Oracle VirtualBox and create an Ubuntu LTS VM. A practical starting point is 2 CPU cores, 4 GB RAM and 25 GB virtual disk (increase RAM if running all monitoring tools and Kubernetes together).
2. Install Ubuntu, update it, and install Git, curl and Docker Engine using the current official Docker Engine instructions for Ubuntu: <https://docs.docker.com/engine/install/ubuntu/>.
3. Add your Ubuntu user to the `docker` group if your lab instructions allow it, then log out/in. Verify with `docker version` and `docker compose version`. If group permissions are not set up, prefix Docker commands with `sudo`.
4. Clone this project inside the VM and run `docker compose up --build -d` as in section 1.
5. To open the dashboard from the host, configure VirtualBox **Settings → Network → Adapter 1 → NAT → Advanced → Port Forwarding**. Add TCP rules for host port `8080` to guest port `8080`, host `3000` to guest `3000`, and host `9090` to guest `9090`. Then use `http://localhost:8080`, `http://localhost:3000` and `http://localhost:9090` on the host. If those ports are already used, choose other host ports and keep the guest ports unchanged.
6. Take a VirtualBox snapshot named `clean-docker-lab` before trying Kubernetes or Terraform. A snapshot is a quick lab rollback point, not a substitute for version control or backups.

VirtualBox networking and Docker installation menus can differ slightly by host OS and version. If you use a bridged adapter instead of NAT, do not expose the service publicly; restrict the VM's network access.

## 4. Version control workflow

Create a repository for the project, then use a branch-based workflow:

```bash
git init
git add .
git commit -m "Initial CloudOps mini lab"
git branch -M main
git remote add origin <your-GitHub-repository-url>
git push -u origin main

git switch -c feature/add-status-field
# Make a small change to app.py, test, then:
pytest -q
git add app.py
git commit -m "Add status field to dashboard API"
git push -u origin feature/add-status-field
```

Open a pull request to `main` and let GitHub Actions run the test job. Merge only after tests pass. After a validated release, tag it:

```bash
git switch main
git pull --ff-only
git tag -a v1.0.0 -m "CloudOps Mini Lab v1.0.0"
git push origin v1.0.0
```

Prefer short, focused commits and meaningful messages. A branch/PR helps review; a tag identifies a release; Git history allows code rollback. It does not roll back external resources or persisted Grafana/Prometheus volumes automatically.

## 5. Test locally

```bash
python3 -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest -q
```

The tests cover the homepage, health/readiness endpoints, status API and metrics endpoint. Tests run in GitHub Actions as well.

## 6. CI/CD: test, build and publish image

Workflow file: `.github/workflows/ci-cd.yml`.

- On a pull request or push to `main`, the `test` job installs Python dependencies and runs `pytest`.
- On a push to `main`, after tests succeed, the `build-and-publish` job builds the Docker image and pushes two tags to GitHub Container Registry (GHCR): a commit-SHA tag and `latest`.
- The workflow uses the repository's built-in `GITHUB_TOKEN`; the publish job grants only `packages: write` in addition to read access to source code.

To enable it, push the project to GitHub and ensure **Settings → Actions → General → Workflow permissions** permit the workflow to use the token. After the first successful build, find the package under the repository owner's GitHub Packages. If package visibility or organization policies restrict publishing, adjust those settings with your instructor/repository admin.

For a VM running Kubernetes, update the manifest image field to the published GHCR image, for example `ghcr.io/your-owner/your-repository:sha-<commit>`, and configure cluster image-pull credentials if the package is private. Pinning a commit tag is more reproducible than always using `latest`.

## 7. Infrastructure as Code with Terraform (optional)

This Terraform configuration creates a Docker image, Docker network and app container. It is separate from Compose and publishes the app on port `8081`; stop/remove any previous Terraform resources before repeating the exercise.

Requirements: Terraform 1.5+ and a running Docker Engine. From the repository root:

```bash
cd infra/terraform
terraform init
terraform fmt -check
terraform validate
terraform plan
terraform apply
# Type yes when prompted
terraform output
```

Open <http://localhost:8081>. Then inspect the actual resources with `docker ps` and `docker network ls`.

```bash
terraform show
terraform destroy
# Type yes when prompted
```

Terraform state records resource identifiers and should be treated as sensitive operational data in real deployments. Do not commit state files; `.gitignore` already excludes them. This local configuration manages Docker resources, not a public cloud account.

## 8. Container orchestration with Kubernetes (optional)

Use a local Minikube cluster on a machine/VM with sufficient resources. This section assumes Minikube is installed and running with Docker available.

```bash
# From repository root, build the local image and load it into Minikube
docker build -t cloudops-mini-lab:local .
minikube image load cloudops-mini-lab:local

kubectl apply -f k8s/deployment.yaml
kubectl get deployments,pods,services
kubectl rollout status deployment/cloudops-mini-lab
minikube service cloudops-mini-lab --url
```

Open the URL returned by `minikube service`. The Deployment requests **two replicas**, uses a rolling update strategy, sets CPU/memory requests and limits, and defines liveness/readiness probes. The Service routes traffic to healthy pods. If a pod exits, the controller works to restore the desired replica count; this is the basic fault-recovery demonstration.

Generate a test request by refreshing the page, then inspect the cluster:

```bash
kubectl get pods -o wide
kubectl describe deployment cloudops-mini-lab
kubectl logs deployment/cloudops-mini-lab --all-pods=true --tail=30
kubectl delete pod <one-pod-name>
kubectl get pods -w
```

The deleted pod should be replaced by the Deployment controller. For a CPU-based Horizontal Pod Autoscaler (HPA), ensure Metrics Server is available (for Minikube, `minikube addons enable metrics-server`) and then apply:

```bash
kubectl apply -f k8s/hpa.yaml
kubectl get hpa -w
```

HPA scale-up requires sufficient CPU load and working resource metrics; it may remain at two replicas when the app is idle. After the exercise:

```bash
kubectl delete -f k8s/hpa.yaml --ignore-not-found
kubectl delete -f k8s/deployment.yaml
```

**Note:** The Kubernetes manifest's `NodePort` is a local lab convenience. The `docker-compose.yml` stack is separate and is not deployed into Kubernetes by these manifests.

## 9. Monitoring, logs and incident-response exercise

1. Open the app, `/health`, `/ready`, and `/api/status`.
2. Open Prometheus at <http://localhost:9090>, search for `cloudops_http_requests_total`, and execute the query. Try `rate(cloudops_http_requests_total[1m])` after generating a few requests.
3. Open Grafana at <http://localhost:3000> and inspect the provisioned dashboard.
4. Run `docker compose logs -f app`. Each HTTP request creates one-line JSON with timestamp, method, path, endpoint and status code.
5. Simulate an incident by stopping the app container: `docker stop cloudops-app`. Check `docker compose ps`, logs, and the dashboard. Restore it with `docker compose start app` (or `docker compose up -d app`).
6. Write a short incident note: symptom, detection, impact, root cause, recovery action and one prevention step.

The app exports a request counter and latency histogram. Prometheus scrapes them every five seconds. The provided dashboard plots request rate, 95th-percentile latency, and request rates grouped by HTTP status. The JSON logs go to stdout/stderr so Docker and Kubernetes logging systems can collect them; this is preferable to hiding logs inside a disposable container filesystem.

## Troubleshooting

- **Port already allocated:** change the host-side port mapping in `docker-compose.yml` (for example `8080:8000` → `8082:8000`) and use the new URL.
- **Docker permission denied on Ubuntu:** try `sudo docker ...`, or add your user to the Docker group according to your lab's security policy and start a new login session.
- **Prometheus target is down:** check `docker compose ps` and `docker compose logs prometheus`; the target inside the Compose network is `app:8000`, not `localhost:8080`.
- **No dashboard data yet:** visit several app endpoints, wait for a scrape interval, then refresh Grafana. Prometheus counters need requests before their rate becomes visible.
- **Terraform image/network conflict:** Compose and Terraform use different app/container/network names, but a prior Terraform apply may still occupy port `8081`; use `terraform destroy` when done.
- **Kubernetes image pull error:** check the image with `minikube image ls`, load it again, and confirm the manifest uses `cloudops-mini-lab:local` with `imagePullPolicy: IfNotPresent`.

## Viva / demonstration checklist

Be prepared to demonstrate and explain:

1. `docker build`, `docker run`/Compose, `docker ps`, `docker inspect`, `docker logs`, `docker exec`, and `docker stats`.
2. The difference between CI (test/build) and CD (publishing a versioned image for deployment).
3. How Terraform's desired-state configuration differs from manually creating a container.
4. Why two Kubernetes replicas plus a Service and probes improve availability compared with a single container (while still not guaranteeing full production fault tolerance).
5. The purpose of metrics, logs, health checks, dashboards and a basic incident-response record.
6. What VirtualBox provides: an isolated guest OS for the lab. Docker containers still share the guest's Linux kernel.
