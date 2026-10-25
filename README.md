Student Expense Tracker

A student-focused web application for recording daily expenses, organizing spending by category, and comparing monthly spending with a monthly budget. The application uses Flask and SQLite, runs in Docker, and has a GitHub Actions workflow that tests the code, builds a Docker image, and publishes it to GitHub Container Registry (GHCR).

Repository: https://github.com/shriya70/studentexpensetracker  
Authors: Shriya Shet and Tejaswini Singh  
Application: Flask + SQLite + HTML/CSS/JavaScript  
DevOps tools: Docker Compose, GitHub Actions, GHCR, Prometheus and Grafana

Features

- Add an expense with an amount, category, date, and description.
- View saved expenses and delete an entry when needed.
- Calculate monthly spending and the number of expenses for the selected/current month.
- Select a month to view spending by category in a pie chart, with category amounts and proportions.
- Set a separate monthly budget. The budget is stored in the browser's local storage, keyed by month.
- Store expense records in SQLite using the expense-data Docker named volume.
- Provide health, readiness, status, and Prometheus metrics endpoints.
- Emit structured application logs to standard output for Docker log inspection.

Expense categories are Food, Transport, College, Shopping, Bills, and Other.

Technology stack

- Python 3.12, Flask, Gunicorn: backend and HTTP API.
- HTML, CSS, JavaScript: browser interface and monthly summaries.
- SQLite: expense record storage.
- Docker and Docker Compose: containerized application and local monitoring stack.
- Git and GitHub: version control and repository hosting.
- GitHub Actions: automated syntax checks, tests, Docker image build, and image publishing.
- Prometheus and Grafana: application metrics and local observability.

Run locally on Windows with Docker Desktop

Prerequisites

Install Git and Docker Desktop. Start Docker Desktop and wait until the Docker Engine is running.

Start the app

Open PowerShell in the project directory and run:

powershell
git clone -b feature/student-expense-tracker https://github.com/shriya70/studentexpensetracker.git
cd studentexpensetracker
docker compose up --build -d
docker compose ps

Open these URLs in your browser:

- Student Expense Tracker: http://localhost:8080
- Health check: http://localhost:8080/health
- Readiness check: http://localhost:8080/ready
- Status JSON: http://localhost:8080/api/status
- Prometheus metrics endpoint: http://localhost:8080/metrics
- Prometheus UI: http://localhost:9090
- Grafana: http://localhost:3000

The local Grafana credentials configured in docker-compose.yml are admin / cloudops123, unless you have changed them. Use this password only for a local lab environment.

Stop the containers

powershell
docker compose down

The named volume expense-data stores the SQLite database at /data/expenses.db, so expense records survive normal container recreation. Avoid docker compose down -v unless you intend to delete the database and monitoring data volumes.

Expense API

| Method | Endpoint           | Purpose                            |
| ------ | ------------------ | ---------------------------------- |
| GET    | /api/expenses      | List saved expense records         |
| POST   | /api/expenses      | Add an expense from a JSON request |
| DELETE | /api/expenses/<id> | Delete an expense by ID            |
| GET    | /health            | Return application health          |
| GET    | /ready             | Check application readiness        |
| GET    | /api/status        | Return service status and uptime   |
| GET    | /metrics           | Expose Prometheus metrics          |

Example PowerShell request to add an expense:

powershell
$body = @{
amount = 150
category = "Food"
note = "Lunch at college"
spent_on = "2026-10-24"
} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8080/api/expenses -Method Post -ContentType "application/json" -Body $body

GitHub Actions CI/CD

The workflow is located at .github/workflows/ci-cd.yml. When a matching push or pull request triggers the workflow, GitHub Actions checks out the repository, sets up Python, installs dependencies, checks Python syntax, runs pytest, and builds a Docker image. On non-pull-request events, it also logs in to GHCR using GitHub's built-in GITHUB_TOKEN and publishes the image.

GHCR image: ghcr.io/shriya70/studentexpensetracker

- GitHub Actions runs (https://github.com/shriya70/studentexpensetracker/actions)
- GitHub Packages for the owner (https://github.com/shriya70?tab=packages)
- Student Expense Tracker package (https://github.com/users/shriya70/packages/container/studentexpensetracker)

To pull the image, first check the package's versions page and use a tag that actually exists:

powershell
docker pull ghcr.io/shriya70/studentexpensetracker:<tag>

Replace <tag> with a published tag shown in GHCR. If the package is private, authenticate to GHCR with an authorized GitHub token before pulling.

Run tests locally

In Windows PowerShell:

powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m py_compile app.py
python -m pytest -q

GitHub Actions runs the configured checks and tests as part of the workflow.

Useful Docker CLI commands

powershell
docker compose ps
docker compose logs --tail 50 app
docker logs -f cloudops-app
docker stats cloudops-app
docker inspect cloudops-app
docker image ls

Project structure

text
.
├── .github/workflows/ci-cd.yml # automated tests, image build and publishing
├── monitoring/
│ ├── prometheus/ # Prometheus configuration
│ └── grafana/ # Grafana data source/dashboard provisioning
├── tests/ # automated tests
├── app.py # Flask app, UI and API routes
├── Dockerfile # application image definition
├── docker-compose.yml # app, Prometheus and Grafana services
├── requirements.txt
└── requirements-dev.txt

Limitations and security notes

- This is an educational mini project, not a production financial application.
- It does not implement accounts or per-user data separation; avoid storing sensitive financial records on a publicly accessible instance.
- Expense records are stored in SQLite, while monthly budget settings are saved in the current browser's local storage. Budget settings therefore do not automatically synchronize between browsers or devices.
- Grafana's default password is intended for local lab use. Change it before any shared or remote deployment.
- Do not expose the development ports directly to the public internet.

Demonstration outline

1. Start the containers with docker compose up --build -d.
2. Add an expense and show the monthly spending summary update.
3. Select a month in the category section and demonstrate the pie chart.
4. Refresh the page to show that expense records remain saved.
5. Show Docker container status/logs and the successful GitHub Actions workflow.
6. Open the GHCR package page to demonstrate published image delivery.
