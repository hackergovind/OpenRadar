import os
import sys
import json
import subprocess
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 8080
BIN_PSQL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "psql.exe")
DB_NAME = "RadarOpus-WinCHIP"
DB_HOST = "127.0.0.1"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASS = "admin123"

def run_query(sql):
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASS
    cmd = [
        BIN_PSQL,
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-d", DB_NAME,
        "-t", "-A",
        "-c", sql
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise Exception(res.stderr.strip() or "Query failed")
    return res.stdout.strip()

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PostgreSQL Database Viewer (RadarOpus-WinCHIP)</title>
<style>
  :root {
    --bg: #0f172a;
    --sidebar-bg: #1e293b;
    --card-bg: #1e293b;
    --border: #334155;
    --text: #f8fafc;
    --text-muted: #94a3b8;
    --primary: #38bdf8;
    --primary-hover: #0ea5e9;
    --accent: #10b981;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    display: flex;
    height: 100vh;
    overflow: hidden;
  }
  #sidebar {
    width: 280px;
    background: var(--sidebar-bg);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
  }
  #sidebar-header {
    padding: 16px;
    border-bottom: 1px solid var(--border);
  }
  #sidebar-header h2 { font-size: 16px; color: var(--primary); margin-bottom: 8px; }
  #search-box {
    width: 100%;
    padding: 8px 12px;
    background: #0f172a;
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-size: 13px;
  }
  #tables-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }
  .table-item {
    padding: 8px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    color: var(--text-muted);
    display: flex;
    justify-content: space-between;
    transition: all 0.15s;
  }
  .table-item:hover { background: #334155; color: var(--text); }
  .table-item.active { background: var(--primary); color: #0f172a; font-weight: 600; }
  
  #main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  #topbar {
    padding: 16px 24px;
    background: var(--card-bg);
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  #current-title { font-size: 18px; font-weight: 600; }
  .actions { display: flex; gap: 10px; align-items: center; }
  button {
    background: var(--primary);
    color: #0f172a;
    border: none;
    padding: 8px 14px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    font-size: 13px;
  }
  button:hover { background: var(--primary-hover); }
  button.secondary {
    background: #334155;
    color: var(--text);
  }
  button.secondary:hover { background: #475569; }
  
  #query-panel {
    padding: 12px 24px;
    background: #1e293b;
    border-bottom: 1px solid var(--border);
    display: flex;
    gap: 8px;
  }
  #sql-input {
    flex: 1;
    padding: 8px 12px;
    background: #0f172a;
    border: 1px solid var(--border);
    border-radius: 6px;
    color: #38bdf8;
    font-family: monospace;
    font-size: 13px;
  }
  
  #content {
    flex: 1;
    overflow: auto;
    padding: 24px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    text-align: left;
  }
  th {
    background: #334155;
    color: var(--primary);
    padding: 10px 14px;
    border: 1px solid var(--border);
    position: sticky;
    top: 0;
    white-space: nowrap;
  }
  td {
    padding: 8px 14px;
    border: 1px solid var(--border);
    max-width: 320px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  tr:nth-child(even) { background: rgba(255, 255, 255, 0.02); }
  tr:hover { background: rgba(56, 189, 248, 0.08); }
  
  #pagination {
    padding: 12px 24px;
    background: var(--card-bg);
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 13px;
    color: var(--text-muted);
  }
  #loader {
    display: none;
    color: var(--primary);
    font-size: 14px;
    padding: 40px;
    text-align: center;
  }
</style>
</head>
<body>

<div id="sidebar">
  <div id="sidebar-header">
    <h2>RadarOpus-WinCHIP</h2>
    <input type="text" id="search-box" placeholder="Search tables..." oninput="filterTables()">
  </div>
  <div id="tables-list"></div>
</div>

<div id="main">
  <div id="topbar">
    <div>
      <span id="current-title">Select a table</span>
      <span id="row-count" style="margin-left: 10px; font-size: 13px; color: var(--text-muted);"></span>
    </div>
    <div class="actions">
      <button class="secondary" onclick="exportCSV()">Export CSV</button>
    </div>
  </div>

  <div id="query-panel">
    <input type="text" id="sql-input" placeholder="Custom SQL, e.g. SELECT * FROM author LIMIT 50;">
    <button onclick="runCustomSQL()">Run Query</button>
  </div>

  <div id="content">
    <div id="loader">Loading data...</div>
    <div id="table-container"></div>
  </div>

  <div id="pagination">
    <span id="page-info">Showing rows 0 - 0</span>
    <div>
      <button class="secondary" id="btn-prev" onclick="prevPage()">Previous</button>
      <button class="secondary" id="btn-next" onclick="nextPage()">Next</button>
    </div>
  </div>
</div>

<script>
let tables = [];
let currentTable = "";
let currentPage = 0;
const pageSize = 50;

async function init() {
  const res = await fetch('/api/tables');
  tables = await res.json();
  renderTables(tables);
  if (tables.length > 0) {
    loadTable(tables[0]);
  }
}

function renderTables(list) {
  const container = document.getElementById('tables-list');
  container.innerHTML = list.map(t => 
    `<div class="table-item ${t === currentTable ? 'active' : ''}" onclick="loadTable('${t}')">${t}</div>`
  ).join('');
}

function filterTables() {
  const q = document.getElementById('search-box').value.toLowerCase();
  const filtered = tables.filter(t => t.toLowerCase().includes(q));
  renderTables(filtered);
}

async function loadTable(tableName) {
  currentTable = tableName;
  currentPage = 0;
  document.getElementById('current-title').textContent = tableName;
  document.querySelectorAll('.table-item').forEach(el => {
    el.classList.toggle('active', el.textContent === tableName);
  });
  fetchData();
}

async function fetchData() {
  const loader = document.getElementById('loader');
  const container = document.getElementById('table-container');
  loader.style.display = 'block';
  container.innerHTML = '';

  const offset = currentPage * pageSize;
  const res = await fetch(`/api/query?table=${encodeURIComponent(currentTable)}&limit=${pageSize}&offset=${offset}`);
  const data = await res.json();
  loader.style.display = 'none';

  if (!data.rows || data.rows.length === 0) {
    container.innerHTML = '<div style="padding: 20px; color: #94a3b8;">No records found.</div>';
    document.getElementById('page-info').textContent = 'Showing 0 rows';
    return;
  }

  const columns = Object.keys(data.rows[0]);
  let html = '<table><thead><tr>';
  columns.forEach(c => html += `<th>${c}</th>`);
  html += '</tr></thead><tbody>';

  data.rows.forEach(r => {
    html += '<tr>';
    columns.forEach(c => {
      const val = r[c] !== null && r[c] !== undefined ? String(r[c]) : '<span style="color:#64748b">NULL</span>';
      html += `<td title="${val.replace(/"/g, '&quot;')}">${val}</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody></table>';
  container.innerHTML = html;

  document.getElementById('page-info').textContent = `Showing ${offset + 1} - ${offset + data.rows.length}`;
  document.getElementById('btn-prev').disabled = currentPage === 0;
  document.getElementById('btn-next').disabled = data.rows.length < pageSize;
}

function prevPage() {
  if (currentPage > 0) {
    currentPage--;
    fetchData();
  }
}

function nextPage() {
  currentPage++;
  fetchData();
}

async function runCustomSQL() {
  const sql = document.getElementById('sql-input').value.trim();
  if (!sql) return;
  const loader = document.getElementById('loader');
  const container = document.getElementById('table-container');
  loader.style.display = 'block';
  container.innerHTML = '';

  const res = await fetch(`/api/raw_query?sql=${encodeURIComponent(sql)}`);
  const data = await res.json();
  loader.style.display = 'none';

  if (data.error) {
    container.innerHTML = `<div style="padding: 20px; color: #ef4444;">Error: ${data.error}</div>`;
    return;
  }

  if (!data.rows || data.rows.length === 0) {
    container.innerHTML = '<div style="padding: 20px; color: #94a3b8;">Query executed, no rows returned.</div>';
    return;
  }

  const columns = Object.keys(data.rows[0]);
  let html = '<table><thead><tr>';
  columns.forEach(c => html += `<th>${c}</th>`);
  html += '</tr></thead><tbody>';

  data.rows.forEach(r => {
    html += '<tr>';
    columns.forEach(c => {
      const val = r[c] !== null && r[c] !== undefined ? String(r[c]) : '<span style="color:#64748b">NULL</span>';
      html += `<td title="${val.replace(/"/g, '&quot;')}">${val}</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody></table>';
  container.innerHTML = html;
  document.getElementById('current-title').textContent = 'Custom SQL Results';
  document.getElementById('page-info').textContent = `${data.rows.length} rows returned`;
}

function exportCSV() {
  if (!currentTable) return;
  window.open(`/api/export_csv?table=${encodeURIComponent(currentTable)}`, '_blank');
}

window.onload = init;
</script>
</body>
</html>
"""

class DBViewerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # quiet logs

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))

        elif path == "/api/tables":
            try:
                raw = run_query("SELECT json_agg(tablename ORDER BY tablename) FROM pg_tables WHERE schemaname = 'public';")
                tables = json.loads(raw) if raw else []
                self.send_json(tables)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        elif path == "/api/query":
            table = qs.get("table", [""])[0]
            limit = int(qs.get("limit", ["50"])[0])
            offset = int(qs.get("offset", ["0"])[0])
            if not table:
                self.send_json({"rows": []})
                return
            try:
                sql = f'SELECT json_agg(t) FROM (SELECT * FROM "{table}" LIMIT {limit} OFFSET {offset}) t;'
                raw = run_query(sql)
                rows = json.loads(raw) if raw and raw != "null" else []
                self.send_json({"rows": rows})
            except Exception as e:
                self.send_json({"error": str(e), "rows": []})

        elif path == "/api/raw_query":
            sql = qs.get("sql", [""])[0]
            if not sql:
                self.send_json({"rows": []})
                return
            try:
                wrapped_sql = f'SELECT json_agg(t) FROM ({sql.rstrip(";")}) t;'
                raw = run_query(wrapped_sql)
                rows = json.loads(raw) if raw and raw != "null" else []
                self.send_json({"rows": rows})
            except Exception as e:
                self.send_json({"error": str(e), "rows": []})

        elif path == "/api/export_csv":
            table = qs.get("table", [""])[0]
            if not table:
                self.send_error(400)
                return
            env = os.environ.copy()
            env["PGPASSWORD"] = DB_PASS
            cmd = [
                BIN_PSQL,
                "-h", DB_HOST,
                "-p", DB_PORT,
                "-U", DB_USER,
                "-d", DB_NAME,
                "-c", f'\\copy "{table}" to stdout with csv header'
            ]
            res = subprocess.run(cmd, env=env, capture_output=True)
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{table}.csv"')
            self.end_headers()
            self.wfile.write(res.stdout)
        else:
            self.send_error(404)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

def main():
    server = HTTPServer(("127.0.0.1", PORT), DBViewerHandler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"Server started at {url}")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
