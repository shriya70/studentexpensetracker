STUDENT EXPENSE TRACKER

A small, practical web application for students to record daily expenses, categorize spending, set a monthly budget, and see where their money goes. The application is containerized with Docker and uses GitHub Actions to run tests, build a Docker image, and publish the image to GitHub Container Registry (GHCR).

Repository: https://github.com/shriya70/studentexpensetracker
Application: Flask + SQLite
Delivery workflow: GitHub Actions + Docker + GHCR

FEATURES

- Add expenses with amount, category, date, and description.
- List recent expenses and delete entries.
- View this month's spending and number of expenses.
- See spending grouped by category.
- Set a monthly budget; the budget preference is saved in the browser's local storage.
- Persist expense records in SQLite using a Docker named volume.
- Expose health, readiness, status, and Prometheus metrics endpoints.
- Send application logs to container stdout for docker compose logs.

Available categories: Food, Transport, College, Shopping, Bills, and Other.

TECH STACK

- Python 3.12, Flask, Gunicorn
- SQLite for expense storage
- Docker and Docker Compose
- Git and GitHub
- GitHub Actions for syntax checks, automated tests, Docker image build, and publishing
- Prometheus and Grafana for local observability

RUN LOCALLY WITH DOCKER DESKTOP

Requirements: Git, Docker Desktop (with the Docker Engine running), and Docker Compose v2.

In PowerShell, run:

git clone -b feature/student-expense-tracker https://github.com/shriya70/studentexpensetracker.git
cd studentexpensetracker
docker compose up --build -d
docker compose ps

Open these pages in your browser:

- Expense Tracker: http://localhost:8080
- Health check: http://localhost:8080/health
- Readiness: http://localhost:8080/ready
- Application status JSON: http://localhost:8080/api/status
- Prometheus metrics: http://localhost:8080/metrics
- Prometheus UI: http://localhost:9090
- Grafana: http://localhost:3000

Grafana lab credentials are admin / cloudops123 unless changed in docker-compose.yml.

To stop the containers:

docker compose down

The named volume expense-data stores /data/expenses.db, so expense records survive normal container recreation. Do not run docker compose down -v unless you intend to delete the stored database and monitoring data.

EXPENSE API

The web interface calls these endpoints:

Method | Endpoint | Purpose
GET | /api/expenses | Return saved expenses
POST | /api/expenses | Add an expense using JSON
DELETE | /api/expenses/<id> | Delete an expense
GET | /health | Health check
GET | /ready | Readiness check
GET | /api/status | Service status and uptime
GET | /metrics | Prometheus metrics

Example request to add an expense:

$body = @{
amount = 150
category = "Food"
note = "Lunch at college"
spent_on = "2026-10-24"
} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8080/api/expenses -Method Post -ContentType "application/json" -Body $body

GITHUB ACTIONS CI/CD

Workflow file: .github/workflows/ci-cd.yml.

For pushes and pull requests, the workflow checks out the code, sets up Python, installs test dependencies, checks Python syntax, runs pytest, and builds the Docker image. On pushes (not pull-request events), it logs in to GHCR with GitHub's built-in GITHUB_TOKEN and publishes the image.

The current workflow creates a branch-based tag and a commit-SHA tag. The image name is:

ghcr.io/shriya70/studentexpensetracker

Find the package from your GitHub profile's Packages tab:

- https://github.com/shriya70?tab=packages
- Direct package page: https://github.com/users/shriya70/packages/container/studentexpensetracker

If the package is not listed, open the latest successful Actions run and confirm the Build and publish Docker image step completed. GitHub Container Registry packages may start with private visibility. If you need public access, open the package page, go to Package settings, and change visibility to Public only if you are comfortable sharing the image.

To pull the image (if you have package access), use a tag shown on the package's versions page:

docker pull ghcr.io/shriya70/studentexpensetracker:<tag>

Replace <tag> with an actual published tag, such as the branch tag or commit-SHA tag listed by GHCR. If the package is private, authenticate to ghcr.io with an authorized GitHub token before pulling.

RUN AUTOMATED TESTS LOCALLY

In Windows PowerShell:

python -m pip install -r requirements.txt -r requirements-dev.txt
python -m py_compile app.py
python -m pytest -q

GitHub Actions runs these checks on every matching push and pull request.

USEFUL DOCKER CLI COMMANDS

docker compose ps
docker compose logs --tail 50 app
docker logs -f cloudops-app
docker stats cloudops-app
docker inspect cloudops-app
docker image ls

PROJECT STRUCTURE

.
├── .github/workflows/ci-cd.yml # CI and GHCR image publishing
├── infra/terraform/ # Optional Terraform lab files
├── k8s/ # Optional Kubernetes lab manifests
├── monitoring/
│ ├── prometheus/ # Prometheus configuration
│ └── grafana/ # Datasource and dashboard provisioning
├── tests/ # Automated tests
├── app.py # Flask application and API
├── Dockerfile # Application image build
├── docker-compose.yml # App + Prometheus + Grafana
├── requirements.txt
└── requirements-dev.txt

The Terraform and Kubernetes files are optional lab extensions inherited from the original CloudOps starter. Review their image names and settings against the current Student Expense Tracker before applying them; the core, verified path is Docker Compose plus GitHub Actions.

LIMITATIONS AND SECURITY NOTES

- This is a student demonstration, not a production finance application.
- There is no login or multi-user separation; do not put sensitive real financial records on a publicly exposed instance.
- The monthly budget preference is stored in the current browser only; expenses are stored in the SQLite database volume.
- The default Grafana password is for local lab use. Change it before any shared or remotely accessible deployment.
- Do not expose these development ports directly to the public internet.

SUGGESTED DEMONSTRATION FLOW

1. Start the stack using docker compose up --build -d.
2. Add an expense in the browser and show the monthly total and category summary update.
3. Refresh the page to show that the expense persists.
4. Use docker compose logs app and the Prometheus/Grafana pages to demonstrate observability.
5. Push a small, safe code change and show the GitHub Actions test/build/publish run.
