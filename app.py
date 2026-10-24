"""A tiny cloud-native service for the CloudOps Mini Lab."""
from __future__ import annotations

import json
import os
import platform
import time
from datetime import datetime, timezone
from time import perf_counter

from flask import Flask, jsonify, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
START_TIME = time.time()
APP_VERSION = os.getenv("APP_VERSION", "dev")
SERVICE_NAME = os.getenv("SERVICE_NAME", "cloudops-mini-lab")

REQUESTS = Counter(
    "cloudops_http_requests_total",
    "Total HTTP requests handled by the CloudOps Mini Lab service",
    ["method", "endpoint", "status"],
)
LATENCY = Histogram(
    "cloudops_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"],
)


def log_event(event: str, **fields: object) -> None:
    """Write one JSON log event to stdout so Docker/Kubernetes can collect it."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO",
        "service": SERVICE_NAME,
        "event": event,
        **fields,
    }
    print(json.dumps(record, default=str), flush=True)


@app.before_request
def mark_request_start() -> None:
    from flask import g
    g.request_started_at = perf_counter()


@app.after_request
def record_request(response: Response) -> Response:
    from flask import request, g
    endpoint = request.endpoint or "unknown"
    status = str(response.status_code)
    REQUESTS.labels(request.method, endpoint, status).inc()
    started = getattr(g, "request_started_at", None)
    if started is not None:
        LATENCY.labels(endpoint).observe(perf_counter() - started)
    log_event(
        "http_request",
        method=request.method,
        path=request.path,
        endpoint=endpoint,
        status_code=response.status_code,
    )
    return response


@app.get("/")
def index() -> str:
    return '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CloudOps Mini Lab</title>
<style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#121e31;--line:#2a3a52;--text:#e7eef8;--muted:#9fb0c7;--accent:#61d6b3}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top right,#18304b 0,transparent 45%),var(--bg);color:var(--text);font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1050px;margin:0 auto;padding:42px 22px}header{display:flex;align-items:center;gap:14px;margin-bottom:32px}.mark{display:grid;place-items:center;width:50px;height:50px;border-radius:14px;background:var(--accent);color:#092119;font-size:24px;font-weight:800}h1{font-size:clamp(28px,4vw,42px);line-height:1.1;margin:0}header p{margin:7px 0 0;color:var(--muted)}.pill{margin-left:auto;border:1px solid #276d5c;color:var(--accent);border-radius:999px;padding:6px 12px;font-size:13px;white-space:nowrap}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}.card{background:linear-gradient(145deg,#17253a,#101a2b);border:1px solid var(--line);border-radius:17px;padding:21px;min-height:130px}.card small{color:var(--muted);display:block;text-transform:uppercase;letter-spacing:.09em;font-size:11px;font-weight:700}.big{font-size:24px;font-weight:700;margin:10px 0 3px;overflow-wrap:anywhere}.sub{font-size:13px;color:var(--muted)}.section{margin-top:25px}.section h2{font-size:18px;margin:0 0 12px}.checks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.check{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:15px;display:flex;gap:12px}.dot{flex:none;width:10px;height:10px;border-radius:50%;background:var(--accent);margin-top:6px;box-shadow:0 0 12px #61d6b355}.check b{display:block;font-size:14px}.check span{color:var(--muted);font-size:13px}.links{display:flex;flex-wrap:wrap;gap:10px}.links a{color:var(--accent);text-decoration:none;border:1px solid var(--line);background:var(--panel);padding:10px 13px;border-radius:10px}.foot{color:var(--muted);font-size:12px;margin-top:28px;border-top:1px solid var(--line);padding-top:15px}code{color:#b6f3df}@media(max-width:700px){.grid{grid-template-columns:1fr}.checks{grid-template-columns:1fr}.pill{display:none}main{padding-top:28px}}
</style></head>
<body><main>
<header><div class="mark">C</div><div><h1>CloudOps Mini Lab</h1><p>A tiny service for practising cloud-native operations.</p></div><div class="pill">● SERVICE ONLINE</div></header>
<div class="grid">
 <article class="card"><small>Service</small><div class="big" id="service">Loading…</div><div class="sub">Application identity</div></article>
 <article class="card"><small>Version</small><div class="big" id="version">Loading…</div><div class="sub">Set by environment / release pipeline</div></article>
 <article class="card"><small>Running on</small><div class="big" id="host">Loading…</div><div class="sub">Container or pod hostname</div></article>
 <article class="card"><small>Uptime</small><div class="big" id="uptime">Loading…</div><div class="sub">Time since this process started</div></article>
 <article class="card"><small>Health</small><div class="big" id="health">Checking…</div><div class="sub">Health and readiness endpoints</div></article>
 <article class="card"><small>Last checked</small><div class="big" id="checked">—</div><div class="sub">Refreshes every five seconds</div></article>
</div>
<section class="section"><h2>Lab capabilities</h2><div class="checks">
 <div class="check"><span class="dot"></span><div><b>Container workflow</b><span>Docker build, run, inspect, logs, exec, and cleanup.</span></div></div>
 <div class="check"><span class="dot"></span><div><b>CI/CD + version control</b><span>Git history, automated tests, and image publishing workflow.</span></div></div>
 <div class="check"><span class="dot"></span><div><b>Infrastructure as Code</b><span>Terraform definitions for a local Docker network and container.</span></div></div>
 <div class="check"><span class="dot"></span><div><b>Orchestration</b><span>Kubernetes deployment with replicas and health probes.</span></div></div>
 <div class="check"><span class="dot"></span><div><b>Monitoring</b><span>Prometheus metrics and a provisioned Grafana dashboard.</span></div></div>
 <div class="check"><span class="dot"></span><div><b>Logs + incident response</b><span>Structured JSON logs collected through container logs.</span></div></div>
</div></section>
<section class="section"><h2>Operations links</h2><div class="links"><a href="/health">Health check ↗</a><a href="/ready">Readiness ↗</a><a href="/api/status">Status API ↗</a><a href="/metrics">Prometheus metrics ↗</a><a href="http://localhost:9090" target="_blank" rel="noreferrer">Prometheus UI ↗</a><a href="http://localhost:3000" target="_blank" rel="noreferrer">Grafana ↗</a></div></section>
<div class="foot">Designed for a student lab. Status checks are local demonstrations, not a production SLA. Metrics and logs intentionally avoid collecting request bodies or personal data.</div>
</main><script>
async function refresh(){try{const r=await fetch('/api/status',{cache:'no-store'});const d=await r.json();document.querySelector('#service').textContent=d.service;document.querySelector('#version').textContent=d.version;document.querySelector('#host').textContent=d.hostname;document.querySelector('#uptime').textContent=d.uptime_human;document.querySelector('#health').textContent=d.status;document.querySelector('#checked').textContent=new Date().toLocaleTimeString();}catch(e){document.querySelector('#health').textContent='Unreachable';}}
refresh();setInterval(refresh,5000);
</script></body></html>'''


@app.get("/health")
def health():
    return jsonify(status="ok", service=SERVICE_NAME), 200


@app.get("/ready")
def ready():
    # Extend this check if the app later depends on a database or another service.
    return jsonify(status="ready", service=SERVICE_NAME), 200


@app.get("/api/status")
def status():
    uptime = max(0, int(time.time() - START_TIME))
    return jsonify(
        service=SERVICE_NAME,
        version=APP_VERSION,
        hostname=platform.node(),
        status="healthy",
        uptime_seconds=uptime,
        uptime_human=f"{uptime // 3600}h {(uptime % 3600) // 60}m {uptime % 60}s",
        checked_at=datetime.now(timezone.utc).isoformat(),
        checks={"process": "ok", "http": "ok", "metrics": "enabled"},
    )


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    # Development only. Production/container uses Gunicorn.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=False)
