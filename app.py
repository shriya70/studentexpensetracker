import json
import os
import platform
import sqlite3
import time
from datetime import date, datetime, timezone
from time import perf_counter

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)
START_TIME = time.time()
APP_VERSION = os.getenv("APP_VERSION", "dev")
SERVICE_NAME = os.getenv("SERVICE_NAME", "student-expense-tracker")
DB_PATH = os.getenv(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db"),
)

REQUESTS = Counter(
    "cloudops_http_requests_total",
    "Total HTTP requests handled by the service",
    ["method", "endpoint", "status"],
)
LATENCY = Histogram(
    "cloudops_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"],
)

ALLOWED_CATEGORIES = {"Food", "Transport", "College", "Shopping", "Bills", "Other"}


def init_db() -> None:
    """Create the expenses database and table if they do not exist yet."""
    parent = os.path.dirname(DB_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                spent_on TEXT NOT NULL
            )"""
        )


def log_event(event: str, **fields: object) -> None:
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
    g.request_started_at = perf_counter()


@app.after_request
def record_request(response: Response) -> Response:
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
<title>Student Expense Tracker</title>
<style>
:root{--bg:#f4f6fb;--panel:#fff;--line:#e4e7f0;--text:#20243a;--muted:#737b91;--accent:#454fc7;--green:#16804a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
header{background:linear-gradient(120deg,#242b5d,#454fc7);color:white;padding:26px max(22px,calc((100% - 1120px)/2))}header h1{margin:0;font-size:clamp(26px,4vw,36px)}header p{margin:6px 0 0;color:#e2e5ff}
main{max-width:1120px;margin:26px auto;padding:0 18px}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-bottom:20px}.card,.panel{background:var(--panel);border:1px solid var(--line);border-radius:15px;padding:20px;box-shadow:0 5px 18px #20243a08}.card small{display:block;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.06em;font-size:11px}.card h2{font-size:clamp(22px,3vw,30px);margin:9px 0 0;overflow-wrap:anywhere}.layout{display:grid;grid-template-columns:minmax(260px,.8fr) minmax(320px,1.5fr);gap:18px}h3{margin:0 0 12px;font-size:18px}label{display:block;margin:13px 0 6px;font-size:13px;font-weight:700}input,select{width:100%;padding:11px;border:1px solid #d6daea;border-radius:8px;font:inherit;background:white;color:var(--text)}button{border:0;border-radius:8px;padding:10px 13px;font:inherit;font-weight:700;cursor:pointer}.primary{background:var(--accent);color:white;width:100%;margin-top:17px}.secondary{background:#eef0ff;color:#303baf}.delete{background:#fff0f0;color:#b42318;padding:7px 9px;font-size:12px}.message{font-size:13px;margin-top:10px;min-height:18px}.error{color:#b42318}.success{color:var(--green)}.muted{color:var(--muted);font-size:13px}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:12px 8px;border-bottom:1px solid #eef0f5;font-size:13px}th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.04em}.amount{white-space:nowrap;font-weight:700}.empty{text-align:center;padding:26px 8px;color:var(--muted)}.budget-area{border-top:1px solid var(--line);margin-top:22px;padding-top:20px}.budget-control{display:flex;gap:8px;align-items:center}.budget-control input{flex:1;min-width:0}.bar{height:8px;background:#e8eaf6;border-radius:9px;overflow:hidden;margin-top:12px}.bar-fill{height:100%;width:0;background:var(--accent);transition:width .2s}.category-line{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid #eef0f5}.category-line:last-child{border-bottom:0}.category-line strong{white-space:nowrap}.section{margin-top:23px}
@media(max-width:760px){.layout{grid-template-columns:1fr}.cards{grid-template-columns:1fr}.card{padding:16px}header{padding:22px}}
</style></head>
<body>
<header><h1>Student Expense Tracker</h1><p>Manage your money, understand your spending, and stay within budget.</p></header>
<main>
<section class="cards">
 <article class="card"><small>This month's spending</small><h2 id="monthlyTotal">₹0.00</h2></article>
 <article class="card"><small>Expenses this month</small><h2 id="expenseCount">0</h2></article>
 <article class="card"><small>Budget remaining</small><h2 id="remaining">₹5,000.00</h2><div class="bar"><div id="budgetBar" class="bar-fill"></div></div><p id="budgetHint" class="muted">Monthly budget progress</p></article>
</section>
<section class="layout">
 <div class="panel">
  <h3>Add an expense</h3>
  <form id="expenseForm">
   <label for="amount">Amount (₹)</label><input id="amount" type="number" min="0.01" max="999999999" step="0.01" placeholder="e.g. 150" required>
   <label for="category">Category</label><select id="category" required><option>Food</option><option>Transport</option><option>College</option><option>Shopping</option><option>Bills</option><option>Other</option></select>
   <label for="spent_on">Date</label><input id="spent_on" type="date" required>
   <label for="note">Description</label><input id="note" maxlength="200" placeholder="e.g. Lunch at college">
   <button class="primary" type="submit">+ Add Expense</button><div id="message" class="message" role="status"></div>
  </form>
  <div class="budget-area"><h3>Monthly budget</h3><p class="muted">Your budget is saved in this browser.</p><label for="budget">Budget (₹)</label><div class="budget-control"><input id="budget" type="number" min="0" max="999999999" step="0.01" value="5000"><button id="saveBudget" class="secondary" type="button">Save</button></div></div>
 </div>
 <div class="panel">
  <h3>Recent expenses</h3><p class="muted">Expense records are saved in the app's SQLite database.</p>
  <div class="table-wrap"><table><thead><tr><th>Date</th><th>Description</th><th>Category</th><th>Amount</th><th></th></tr></thead><tbody id="expenseRows"><tr><td colspan="5" class="empty">Loading expenses…</td></tr></tbody></table></div>
  <section class="section"><h3>Spending by category</h3><div id="categorySummary" class="muted">Loading summary…</div></section>
 </div>
</section>
<p class="muted" style="text-align:center;margin:22px 0">Student Expense Tracker · Flask + SQLite · Dockerized application</p>
</main>
<script>
const money=value=>Number(value).toLocaleString('en-IN',{style:'currency',currency:'INR'});
const now=new Date();document.getElementById('spent_on').value=[now.getFullYear(),String(now.getMonth()+1).padStart(2,'0'),String(now.getDate()).padStart(2,'0')].join('-');
let expenses=[];let budget=Number(localStorage.getItem('studentBudget')||5000);document.getElementById('budget').value=budget;
function message(text,type){const el=document.getElementById('message');el.textContent=text;el.className='message '+type;}
async function loadExpenses(){const response=await fetch('/api/expenses',{cache:'no-store'});if(!response.ok)throw new Error('Could not load expenses');expenses=await response.json();render();}
function render(){const d=new Date(),month=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0');const monthly=expenses.filter(e=>e.spent_on.startsWith(month));const total=monthly.reduce((s,e)=>s+Number(e.amount),0);document.getElementById('monthlyTotal').textContent=money(total);document.getElementById('expenseCount').textContent=monthly.length;document.getElementById('remaining').textContent=money(budget-total);document.getElementById('budgetBar').style.width=Math.min(budget>0?total/budget*100:(total>0?100:0),100)+'%';document.getElementById('budgetHint').textContent=budget>0?Math.round(total/budget*100)+'% of monthly budget used':(total>0?'Budget exceeded':'No budget set');
const rows=document.getElementById('expenseRows');rows.replaceChildren();if(!expenses.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=5;td.className='empty';td.textContent='No expenses yet. Add your first expense!';tr.appendChild(td);rows.appendChild(tr);}expenses.forEach(e=>{const tr=document.createElement('tr');[e.spent_on,e.note||'Expense',e.category].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.appendChild(td);});const amount=document.createElement('td');amount.className='amount';amount.textContent=money(e.amount);tr.appendChild(amount);const action=document.createElement('td'),btn=document.createElement('button');btn.className='delete';btn.textContent='Delete';btn.addEventListener('click',()=>deleteExpense(e.id));action.appendChild(btn);tr.appendChild(action);rows.appendChild(tr);});
const totals={};monthly.forEach(e=>totals[e.category]=(totals[e.category]||0)+Number(e.amount));const summary=document.getElementById('categorySummary');summary.replaceChildren();const keys=Object.keys(totals).sort();if(!keys.length){summary.textContent='No spending recorded this month.';}else{keys.forEach(k=>{const line=document.createElement('div'),name=document.createElement('span'),val=document.createElement('strong');line.className='category-line';name.textContent=k;val.textContent=money(totals[k]);line.append(name,val);summary.appendChild(line);});}}
document.getElementById('expenseForm').addEventListener('submit',async e=>{e.preventDefault();const payload={amount:Number(document.getElementById('amount').value),category:document.getElementById('category').value,spent_on:document.getElementById('spent_on').value,note:document.getElementById('note').value.trim()};try{const r=await fetch('/api/expenses',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const result=await r.json();if(!r.ok)throw new Error(result.error||'Could not add expense');document.getElementById('amount').value='';document.getElementById('note').value='';message('Expense added successfully.','success');await loadExpenses();}catch(err){message(err.message,'error');}});
async function deleteExpense(id){if(!confirm('Delete this expense?'))return;try{const r=await fetch('/api/expenses/'+id,{method:'DELETE'});const result=await r.json();if(!r.ok)throw new Error(result.error||'Could not delete expense');message('Expense deleted.','success');await loadExpenses();}catch(err){message(err.message,'error');}}
document.getElementById('saveBudget').addEventListener('click',()=>{const value=Number(document.getElementById('budget').value);if(!Number.isFinite(value)||value<0||value>999999999){message('Enter a valid budget between ₹0 and ₹999,999,999.','error');return;}budget=value;localStorage.setItem('studentBudget',String(budget));message('Budget saved.','success');render();});
loadExpenses().catch(err=>{document.getElementById('expenseRows').innerHTML='<tr><td colspan="5" class="empty">Could not load expenses. Check the server logs.</td></tr>';message(err.message,'error');});
</script></body></html>'''


@app.get("/api/expenses")
def get_expenses():
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            "SELECT id, amount, category, note, spent_on FROM expenses ORDER BY spent_on DESC, id DESC"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/expenses")
def add_expense():
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get("amount", 0))
        category = str(data.get("category", "")).strip()
        note = str(data.get("note", "")).strip()
        spent_on = str(data.get("spent_on", date.today().isoformat()))
        if not (0 < amount < 1_000_000_000):
            return jsonify(error="Enter a valid positive amount"), 400
        if category not in ALLOWED_CATEGORIES:
            return jsonify(error="Invalid category"), 400
        if len(note) > 200:
            return jsonify(error="Note must be 200 characters or fewer"), 400
        parsed_date = date.fromisoformat(spent_on)
        if parsed_date.isoformat() != spent_on:
            raise ValueError("Date must use YYYY-MM-DD format")
    except (ValueError, TypeError):
        return jsonify(error="Invalid amount or date"), 400

    with sqlite3.connect(DB_PATH) as db:
        cursor = db.execute(
            "INSERT INTO expenses (amount, category, note, spent_on) VALUES (?, ?, ?, ?)",
            (amount, category, note, spent_on),
        )
        expense_id = cursor.lastrowid
    return jsonify(id=expense_id, message="Expense added"), 201


@app.delete("/api/expenses/<int:expense_id>")
def delete_expense(expense_id: int):
    with sqlite3.connect(DB_PATH) as db:
        cursor = db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    if cursor.rowcount == 0:
        return jsonify(error="Expense not found"), 404
    return jsonify(message="Expense deleted")


@app.get("/health")
def health():
    return jsonify(status="ok", service=SERVICE_NAME), 200


@app.get("/ready")
def ready():
    try:
        with sqlite3.connect(DB_PATH) as db:
            db.execute("SELECT 1")
        return jsonify(status="ready", service=SERVICE_NAME), 200
    except sqlite3.Error:
        return jsonify(status="not_ready", service=SERVICE_NAME), 503


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
        checks={"process": "ok", "database": "ok", "metrics": "enabled"},
    )


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


# Ensure the database exists when Gunicorn imports this module.
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=False)
