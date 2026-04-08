from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.utils
import json
import re
import socket
import os
import random
from datetime import datetime, timedelta

# ------------------------------------------------------------
# 1. Gemini Setup (optional)
# ------------------------------------------------------------
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. Install with: pip install google-generativeai")

# Set your API key here OR via environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")   # replace with "AIza..." if you want
if GEMINI_API_KEY and GEMINI_AVAILABLE:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    print("✓ Gemini AI ready")
else:
    model = None
    if GEMINI_API_KEY and not GEMINI_AVAILABLE:
        print("✗ Gemini library missing – install it to use AI.")
    else:
        print("ℹ️ No Gemini API key – using rule‑based SQL generator only.")

# ------------------------------------------------------------
# 2. FastAPI App
# ------------------------------------------------------------
app = FastAPI(title="NL2SQL Chatbot", version="2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# 3. Database Setup (realistic data, 200+ rows)
# ------------------------------------------------------------
def create_full_database():
    """Creates clinic.db with 200 patients, 15 doctors, 500 appointments, etc."""
    if os.path.exists("clinic.db"):
        print("✓ Database already exists")
        return

    conn = sqlite3.connect("clinic.db")
    cursor = conn.cursor()

    # --- tables ---
    cursor.executescript('''
        CREATE TABLE patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT, last_name TEXT, email TEXT, phone TEXT,
            date_of_birth DATE, gender TEXT, city TEXT, registered_date DATE
        );
        CREATE TABLE doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, specialization TEXT, department TEXT, phone TEXT
        );
        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER, doctor_id INTEGER,
            appointment_date DATETIME, status TEXT, notes TEXT
        );
        CREATE TABLE treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER, treatment_name TEXT,
            cost REAL, duration_minutes INTEGER
        );
        CREATE TABLE invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER, invoice_date DATE,
            total_amount REAL, paid_amount REAL, status TEXT
        );
    ''')

    # --- doctors (15) ---
    doctors = [
        ("Dr. Sarah Johnson", "Dermatology", "Skin Care", "555-0101"),
        ("Dr. Michael Lee", "Dermatology", "Skin Care", "555-0102"),
        ("Dr. James Wilson", "Cardiology", "Heart Center", "555-0201"),
        ("Dr. Maria Garcia", "Cardiology", "Heart Center", "555-0202"),
        ("Dr. Jennifer Martinez", "Orthopedics", "Bone & Joint", "555-0301"),
        ("Dr. David Anderson", "Orthopedics", "Bone & Joint", "555-0302"),
        ("Dr. Richard Jackson", "General", "Primary Care", "555-0401"),
        ("Dr. Patricia White", "General", "Primary Care", "555-0402"),
        ("Dr. Susan Martin", "Pediatrics", "Children's Health", "555-0501"),
        ("Dr. Paul Thompson", "Pediatrics", "Children's Health", "555-0502"),
        ("Dr. Robert Taylor", "Cardiology", "Heart Center", "555-0203"),
        ("Dr. Lisa Thomas", "Orthopedics", "Bone & Joint", "555-0303"),
        ("Dr. Charles Harris", "General", "Primary Care", "555-0403"),
        ("Dr. Karen Robinson", "Pediatrics", "Children's Health", "555-0503"),
        ("Dr. Emily Brown", "Dermatology", "Skin Care", "555-0103"),
    ]
    cursor.executemany('INSERT INTO doctors (name, specialization, department, phone) VALUES (?,?,?,?)', doctors)

    # --- patients (200) ---
    first_names = ["John","Jane","Michael","Emily","David","Sarah","Robert","Lisa","James","Maria",
                   "William","Jennifer","Richard","Patricia","Charles","Susan","Thomas","Karen","Daniel","Linda"]
    last_names = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez"]
    cities = ["New York","Los Angeles","Chicago","Houston","Phoenix","Philadelphia","San Antonio","San Diego","Dallas","Austin"]
    genders = ["M","F"]
    patients = []
    for i in range(200):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        email = f"{fn.lower()}.{ln.lower()}{random.randint(1,999)}@example.com" if random.random()>0.1 else None
        phone = f"555-{random.randint(100,999)}-{random.randint(1000,9999)}" if random.random()>0.05 else None
        dob = f"{random.randint(1950,2010)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        gender = random.choice(genders)
        city = random.choice(cities)
        reg_date = (datetime.now() - timedelta(days=random.randint(0,365))).strftime("%Y-%m-%d")
        patients.append((fn, ln, email, phone, dob, gender, city, reg_date))
    cursor.executemany('''
        INSERT INTO patients (first_name, last_name, email, phone, date_of_birth, gender, city, registered_date)
        VALUES (?,?,?,?,?,?,?,?)
    ''', patients)
    patient_ids = list(range(1,201))

    # --- appointments (500) ---
    statuses = ["Scheduled","Completed","Cancelled","No-Show"]
    weights = [0.3,0.5,0.1,0.1]
    appointments = []
    for _ in range(500):
        pid = random.choice(patient_ids)
        did = random.randint(1,15)
        days_ago = random.randint(0,365)
        apt_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        status = random.choices(statuses, weights=weights)[0]
        notes = f"Notes for apt {_+1}" if random.random()>0.7 else None
        appointments.append((pid, did, apt_date, status, notes))
    cursor.executemany('INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes) VALUES (?,?,?,?,?)', appointments)
    cursor.execute("SELECT id FROM appointments WHERE status='Completed'")
    completed_ids = [row[0] for row in cursor.fetchall()]

    # --- treatments (one per completed appointment, up to 350) ---
    treatments_list = ["Check-up","X-Ray","Blood Test","MRI","CT Scan","Physical Therapy","Vaccination","ECG","Ultrasound"]
    treatments = []
    for aid in completed_ids[:350]:
        name = random.choice(treatments_list)
        cost = round(random.uniform(50,5000),2)
        duration = random.choice([15,30,45,60,90])
        treatments.append((aid, name, cost, duration))
    cursor.executemany('INSERT INTO treatments (appointment_id, treatment_name, cost, duration_minutes) VALUES (?,?,?,?)', treatments)

    # --- invoices (300) ---
    inv_statuses = ["Paid","Pending","Overdue"]
    inv_weights = [0.5,0.3,0.2]
    invoices = []
    for _ in range(300):
        pid = random.choice(patient_ids)
        inv_date = (datetime.now() - timedelta(days=random.randint(0,365))).strftime("%Y-%m-%d")
        total = round(random.uniform(100,10000),2)
        status = random.choices(inv_statuses, weights=inv_weights)[0]
        paid = total if status=="Paid" else round(total*random.uniform(0,0.5),2) if status=="Pending" else 0
        invoices.append((pid, inv_date, total, paid, status))
    cursor.executemany('INSERT INTO invoices (patient_id, invoice_date, total_amount, paid_amount, status) VALUES (?,?,?,?,?)', invoices)

    conn.commit()
    conn.close()
    print("✓ Full database created: 200 patients, 15 doctors, 500 appointments, 350 treatments, 300 invoices")

# ------------------------------------------------------------
# 4. SQL Validation & Charting
# ------------------------------------------------------------
DANGEROUS_KEYWORDS = ["INSERT","UPDATE","DELETE","DROP","ALTER","CREATE","EXEC","GRANT","REVOKE"]
SYSTEM_TABLES = ["sqlite_master","sqlite_sequence"]

def validate_sql(sql: str):
    if not sql: return False, "Empty SQL"
    sql_up = sql.upper().strip()
    if not sql_up.startswith("SELECT"): return False, "Only SELECT allowed"
    for kw in DANGEROUS_KEYWORDS:
        if kw in sql_up: return False, f"Dangerous keyword '{kw}'"
    for tbl in SYSTEM_TABLES:
        if tbl in sql.lower(): return False, f"System table '{tbl}' not allowed"
    return True, ""

def generate_chart(df: pd.DataFrame):
    if df.empty or len(df.columns)<2: return None
    try:
        numeric = df.select_dtypes(include='number').columns.tolist()
        cat = df.select_dtypes(include='object').columns.tolist()
        if not numeric: return None
        if len(df)<=10 and cat:
            fig = px.bar(df, x=cat[0], y=numeric[0], title="Results")
        elif len(numeric)>=2:
            fig = px.scatter(df, x=numeric[0], y=numeric[1], title="Results")
        else:
            fig = px.line(df, x=df.index, y=numeric[0], title="Results")
        return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))
    except: return None

# ------------------------------------------------------------
# 5. SQL Generation – Gemini + Rule‑Based Fallback
# ------------------------------------------------------------
def fallback_sql(question: str) -> str:
    q = question.lower()
    # Most common questions
    if "how many patients" in q or "patient count" in q:
        return "SELECT COUNT(*) AS patient_count FROM patients"
    if "list all doctors" in q or "all doctors" in q:
        return "SELECT id, name, specialization, department FROM doctors"
    if "total revenue" in q:
        return "SELECT SUM(total_amount) AS total_revenue FROM invoices WHERE status='Paid'"
    if "revenue by doctor" in q:
        return """SELECT d.name, SUM(i.total_amount) AS revenue
                  FROM doctors d
                  JOIN appointments a ON d.id = a.doctor_id
                  JOIN invoices i ON a.patient_id = i.patient_id
                  WHERE i.status='Paid'
                  GROUP BY d.id"""
    if "most appointments" in q or "busiest doctor" in q:
        return """SELECT d.name, COUNT(a.id) AS cnt
                  FROM doctors d
                  JOIN appointments a ON d.id = a.doctor_id
                  GROUP BY d.id ORDER BY cnt DESC LIMIT 1"""
    if "cancelled appointments" in q:
        return "SELECT COUNT(*) AS cancelled FROM appointments WHERE status='Cancelled'"
    if "top patients by spending" in q or "top 5 patients" in q:
        return """SELECT p.first_name, p.last_name, SUM(i.total_amount) AS spent
                  FROM patients p
                  JOIN invoices i ON p.id = i.patient_id
                  WHERE i.status='Paid'
                  GROUP BY p.id ORDER BY spent DESC LIMIT 5"""
    if "city" in q and "most patients" in q:
        return "SELECT city, COUNT(*) AS cnt FROM patients GROUP BY city ORDER BY cnt DESC LIMIT 1"
    if "last month appointments" in q:
        return """SELECT * FROM appointments
                  WHERE appointment_date >= date('now','-1 month')
                  AND appointment_date < date('now')"""
    # default
    return "SELECT * FROM patients LIMIT 5"

def generate_sql(question: str) -> str:
    """Try Gemini, fallback to rule-based"""
    if model is None:
        return fallback_sql(question)

    prompt = f"""You are an expert SQLite assistant. Given this schema, answer with ONLY a SELECT SQL query, no explanation.

Schema:
- patients(id, first_name, last_name, email, phone, date_of_birth, gender, city, registered_date)
- doctors(id, name, specialization, department, phone)
- appointments(id, patient_id, doctor_id, appointment_date, status, notes)
- treatments(id, appointment_id, treatment_name, cost, duration_minutes)
- invoices(id, patient_id, invoice_date, total_amount, paid_amount, status)

User: {question}
SQL:"""
    try:
        resp = model.generate_content(prompt)
        sql = resp.text.strip()
        # clean markdown
        sql = re.sub(r'```sql\s*|```', '', sql)
        sql = sql.strip()
        if not sql or len(sql) < 6:
            return fallback_sql(question)
        if not sql.upper().startswith("SELECT"):
            match = re.search(r'SELECT\s+.*', sql, re.IGNORECASE)
            if match:
                sql = match.group(0)
            else:
                return fallback_sql(question)
        return sql
    except Exception as e:
        print(f"Gemini error: {e}")
        return fallback_sql(question)

# ------------------------------------------------------------
# 6. Pydantic models
# ------------------------------------------------------------
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    message: str
    sql_query: Optional[str] = None
    columns: Optional[List[str]] = None
    rows: Optional[List[List[Any]]] = None
    row_count: int = 0
    chart: Optional[Dict] = None

# ------------------------------------------------------------
# 7. Web UI (same as before)
# ------------------------------------------------------------
HTML_UI = """<!DOCTYPE html>
<html>
<head><title>NL2SQL Chatbot</title>
<style>
body { font-family: Arial; max-width: 1200px; margin: 40px auto; padding: 20px; }
textarea { width: 100%; padding: 10px; margin: 10px 0; }
button { background: #007bff; color: white; border: none; padding: 10px 20px; cursor: pointer; margin: 5px; }
.example-btn { background: #28a745; }
pre { background: #f4f4f4; padding: 10px; overflow-x: auto; }
table { border-collapse: collapse; width: 100%; margin-top: 10px; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background-color: #f2f2f2; }
.result-box { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }
.error { color: red; }
</style>
</head>
<body>
<h1>NL2SQL Chatbot (Gemini + Fallback)</h1>
<p>Ask questions about patients, doctors, appointments, revenue...</p>
<div>
    <button class="example-btn" onclick="setQuestion('How many patients do we have?')">1. Patient count</button>
    <button class="example-btn" onclick="setQuestion('List all doctors and their specializations')">2. Doctors</button>
    <button class="example-btn" onclick="setQuestion('Show me appointments for last month')">3. Last month appointments</button>
    <button class="example-btn" onclick="setQuestion('Which doctor has the most appointments?')">4. Busiest doctor</button>
    <button class="example-btn" onclick="setQuestion('What is the total revenue?')">5. Total revenue</button>
    <button class="example-btn" onclick="setQuestion('Show revenue by doctor')">6. Revenue by doctor</button>
    <button class="example-btn" onclick="setQuestion('How many cancelled appointments?')">7. Cancelled</button>
    <button class="example-btn" onclick="setQuestion('Top 5 patients by spending')">8. Top patients</button>
    <button class="example-btn" onclick="setQuestion('Which city has the most patients?')">9. City with most patients</button>
</div>
<textarea id="question" rows="3" placeholder="Ask a question..."></textarea>
<button onclick="askQuestion()">Ask</button>
<div id="result" class="result-box"><h3>Response:</h3><div id="responseContent">Waiting...</div></div>
<script>
function setQuestion(q) { document.getElementById('question').value = q; askQuestion(); }
async function askQuestion() {
    const question = document.getElementById('question').value;
    const respDiv = document.getElementById('responseContent');
    respDiv.innerHTML = '<p>Processing...</p>';
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });
        const data = await response.json();
        if (response.ok) {
            let html = `<p><strong>${data.message}</strong></p>`;
            if (data.sql_query) html += `<h4>SQL:</h4><pre>${escapeHtml(data.sql_query)}</pre>`;
            if (data.columns && data.rows && data.rows.length) {
                html += `<h4>Results (${data.row_count} rows):</h4><table><tr>${data.columns.map(c=>`<th>${escapeHtml(c)}</th>`).join('')}</tr>`;
                data.rows.forEach(row => html += `<tr>${row.map(c=>`<td>${escapeHtml(String(c))}</td>`).join('')}</tr>`);
                html += `</table>`;
            } else if (data.row_count === 0) html += `<p>No data found.</p>`;
            if (data.chart) {
                html += `<div id="chart"></div>`;
                respDiv.innerHTML = html;
                Plotly.newPlot('chart', data.chart.data, data.chart.layout);
                return;
            }
            respDiv.innerHTML = html;
        } else {
            respDiv.innerHTML = `<p class="error">Error: ${data.detail}</p>`;
        }
    } catch(err) {
        respDiv.innerHTML = `<p class="error">Request failed: ${err.message}</p>`;
    }
}
function escapeHtml(str) { return str.replace(/[&<>]/g, m => m==='&'?'&amp;':m==='<'?'&lt;':'&gt;'); }
</script>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</body>
</html>"""

# ------------------------------------------------------------
# 8. API Endpoints
# ------------------------------------------------------------
@app.on_event("startup")
async def startup():
    create_full_database()

@app.get("/", response_class=HTMLResponse)
async def ui():
    return HTML_UI

@app.get("/health")
async def health():
    return {"status": "ok", "db_exists": os.path.exists("clinic.db"), "gemini_ready": model is not None}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    q = req.question.strip()
    if not q:
        return ChatResponse(message="Question empty.")

    sql = generate_sql(q)
    if not sql:
        return ChatResponse(message="Could not generate SQL (even fallback failed).")

    valid, err = validate_sql(sql)
    if not valid:
        return ChatResponse(message=f"SQL invalid: {err}", sql_query=sql)

    try:
        conn = sqlite3.connect("clinic.db")
        df = pd.read_sql_query(sql, conn)
        conn.close()
        cols = df.columns.tolist()
        rows = df.values.tolist()[:20]
        cnt = len(df)
        chart = generate_chart(df) if cnt > 0 else None
        msg = f"Found {cnt} result(s)." + (" Showing first 20." if cnt>20 else "")
        return ChatResponse(message=msg, sql_query=sql, columns=cols, rows=rows, row_count=cnt, chart=chart)
    except Exception as e:
        return ChatResponse(message=f"DB error: {str(e)}", sql_query=sql)

# ------------------------------------------------------------
# 9. Run Server
# ------------------------------------------------------------
def find_free_port(start=8001, end=9000):
    for port in range(start, end+1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port")

if __name__ == "__main__":
    import uvicorn
    port = find_free_port()
    print(f"\n🚀 Server running at http://localhost:{port}")
    print(f"📖 API docs: http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port)