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

def run_query_json(sql):
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASS
    cleaned_sql = sql.strip().rstrip(";")
    wrapped = f"SELECT json_agg(t) FROM ({cleaned_sql}) t;"
    cmd = [
        BIN_PSQL,
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-d", DB_NAME,
        "-t", "-A",
        "-c", wrapped
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise Exception(res.stderr.strip() or "Query failed")
    raw = res.stdout.strip()
    if not raw or raw == "null":
        return []
    return json.loads(raw)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RadarOpus - Synthesis Repertory & Analysis System</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
  :root {
    --ro-topbar-bg: #2b3e50;
    --ro-nav-bg: #34495e;
    --ro-panel-bg: #f8fafc;
    --ro-border: #cbd5e1;
    --ro-active-blue: #0284c7;
    --ro-active-hover: #0369a1;
    --ro-text-main: #1e293b;
    --ro-text-muted: #64748b;
    --grade4-color: #dc2626; /* Red bold underlined */
    --grade3-color: #2563eb; /* Bold Blue */
    --grade2-color: #0d9488; /* Italics Teal */
    --grade1-color: #475569; /* Normal Grey */
  }

  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  body { height: 100vh; display: flex; flex-direction: column; background: #e2e8f0; color: var(--ro-text-main); overflow: hidden; }

  /* RadarOpus Top Bar & Toolbar */
  #ro-header {
    background: var(--ro-topbar-bg);
    color: #fff;
    display: flex;
    flex-direction: column;
    box-shadow: 0 2px 4px rgba(0,0,0,0.15);
    z-index: 10;
  }
  .ro-menubar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 14px;
    background: #1e293b;
    font-size: 13px;
  }
  .ro-brand { font-weight: 700; display: flex; align-items: center; gap: 8px; font-size: 14px; color: #38bdf8; letter-spacing: 0.5px; }
  .ro-brand span { color: #f1f5f9; font-weight: 400; font-size: 12px; }

  .ro-toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    background: #283747;
    border-top: 1px solid rgba(255,255,255,0.08);
  }
  .ro-tool-btn {
    background: #34495e;
    border: 1px solid rgba(255,255,255,0.15);
    color: #f1f5f9;
    padding: 5px 12px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.15s;
  }
  .ro-tool-btn:hover { background: #415b76; color: #fff; }
  .ro-tool-btn.active { background: var(--ro-active-blue); border-color: #38bdf8; }

  .ro-search-container {
    flex: 1;
    display: flex;
    align-items: center;
    background: #fff;
    border-radius: 5px;
    padding: 2px 8px;
    margin: 0 16px;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);
  }
  .ro-search-container i { color: #64748b; font-size: 14px; margin-right: 6px; }
  #global-search-input {
    width: 100%;
    border: none;
    outline: none;
    padding: 6px 4px;
    font-size: 13px;
    color: #0f172a;
  }

  /* Clipboards Tab Strip */
  .ro-clipboards-bar {
    display: flex;
    background: #1e293b;
    padding: 0 14px;
    border-top: 1px solid #334155;
    gap: 2px;
  }
  .ro-clip-tab {
    padding: 6px 14px;
    font-size: 12px;
    color: #94a3b8;
    background: #253342;
    cursor: pointer;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
    border: 1px solid transparent;
    border-bottom: none;
  }
  .ro-clip-tab:hover { color: #f1f5f9; background: #2c3e50; }
  .ro-clip-tab.active { background: #f8fafc; color: #0284c7; font-weight: 600; border-color: #cbd5e1; }
  .ro-clip-tab .badge { background: #0284c7; color: white; border-radius: 10px; padding: 1px 6px; font-size: 10px; font-weight: bold; }

  /* Main 3-Column Layout (Chapters | Rubrics & Remedies | Repertorization Grid) */
  #ro-main-workspace {
    flex: 1;
    display: flex;
    overflow: hidden;
  }

  /* Col 1: Chapters Sidebar */
  #chapters-sidebar {
    width: 230px;
    background: #ffffff;
    border-right: 1px solid var(--ro-border);
    display: flex;
    flex-direction: column;
  }
  .sidebar-title {
    padding: 10px 14px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    color: #64748b;
    background: #f1f5f9;
    border-bottom: 1px solid var(--ro-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  #chapters-list {
    flex: 1;
    overflow-y: auto;
    list-style: none;
  }
  .chapter-item {
    padding: 8px 14px;
    font-size: 12.5px;
    color: #334155;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid #f1f5f9;
    transition: background 0.1s;
  }
  .chapter-item:hover { background: #e0f2fe; color: #0369a1; }
  .chapter-item.active { background: #bae6fd; color: #0369a1; font-weight: 600; border-left: 3px solid #0284c7; }

  /* Col 2: Rubric Explorer & Remedies Display */
  #rubric-explorer-col {
    flex: 1;
    background: #ffffff;
    border-right: 1px solid var(--ro-border);
    display: flex;
    flex-direction: column;
    min-width: 380px;
  }
  .explorer-header {
    padding: 10px 14px;
    background: #f8fafc;
    border-bottom: 1px solid var(--ro-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .breadcrumb-path {
    font-size: 13px;
    font-weight: 600;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }
  .breadcrumb-path span { color: #64748b; font-weight: normal; }

  /* Search & Rubric List */
  #rubrics-filter-box {
    padding: 8px 12px;
    background: #f1f5f9;
    border-bottom: 1px solid var(--ro-border);
  }
  #rubrics-filter-input {
    width: 100%;
    padding: 6px 10px;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    font-size: 12.5px;
    outline: none;
  }
  #rubrics-list {
    flex: 1;
    overflow-y: auto;
    border-bottom: 1px solid var(--ro-border);
  }
  .rubric-row {
    padding: 8px 12px;
    font-size: 12.5px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #f1f5f9;
  }
  .rubric-row:hover { background: #f8fafc; }
  .rubric-row.active { background: #e0f2fe; font-weight: 600; color: #0369a1; border-left: 3px solid #0284c7; }
  .rubric-text { flex: 1; padding-right: 10px; }
  .rubric-badge {
    background: #e2e8f0;
    color: #475569;
    font-size: 11px;
    padding: 2px 6px;
    border-radius: 10px;
    font-weight: 600;
  }
  .add-to-clip-btn {
    background: #e0f2fe;
    color: #0369a1;
    border: 1px solid #7dd3fc;
    border-radius: 3px;
    padding: 2px 7px;
    font-size: 11px;
    cursor: pointer;
    margin-left: 8px;
    display: none;
  }
  .rubric-row:hover .add-to-clip-btn { display: inline-block; }
  .add-to-clip-btn:hover { background: #0284c7; color: #fff; }

  /* Selected Rubric Remedies Box */
  #rubric-remedies-view {
    height: 45%;
    display: flex;
    flex-direction: column;
    background: #fcfcfc;
    border-top: 2px solid #e2e8f0;
  }
  .remedies-header-bar {
    padding: 8px 14px;
    background: #f1f5f9;
    border-bottom: 1px solid var(--ro-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    font-weight: 600;
  }
  .remedy-filters {
    display: flex;
    gap: 6px;
    align-items: center;
  }
  .remedy-filters select, .remedy-filters input {
    font-size: 11px;
    padding: 3px 6px;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
  }
  #remedies-container {
    flex: 1;
    overflow-y: auto;
    padding: 12px 14px;
    line-height: 1.8;
    font-size: 13px;
  }
  .remedy-tag {
    display: inline-block;
    padding: 2px 6px;
    margin: 2px 4px;
    border-radius: 3px;
    cursor: pointer;
    transition: transform 0.1s;
    user-select: none;
  }
  .remedy-tag:hover { transform: scale(1.08); }
  .remedy-grade-4 { color: var(--grade4-color); font-weight: 800; text-decoration: underline; background: #fee2e2; }
  .remedy-grade-3 { color: var(--grade3-color); font-weight: 700; background: #dbeafe; }
  .remedy-grade-2 { color: var(--grade2-color); font-style: italic; background: #ccfbf1; }
  .remedy-grade-1 { color: var(--grade1-color); font-weight: 400; background: #f1f5f9; }

  /* Col 3: RadarOpus Repertorization Sheet (The Core Grid) */
  #repertorization-col {
    width: 480px;
    background: #ffffff;
    display: flex;
    flex-direction: column;
  }
  .rep-header {
    padding: 10px 14px;
    background: #f8fafc;
    border-bottom: 1px solid var(--ro-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .rep-header h3 { font-size: 13px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 6px; }
  .rep-actions { display: flex; gap: 6px; }
  .btn-sm {
    font-size: 11px;
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid #cbd5e1;
    background: #f8fafc;
    color: #334155;
    cursor: pointer;
    font-weight: 600;
  }
  .btn-sm:hover { background: #e2e8f0; }
  .btn-primary-sm { background: #0284c7; color: white; border-color: #0369a1; }
  .btn-primary-sm:hover { background: #0369a1; }

  /* Repertorization Matrix Table */
  #matrix-wrapper {
    flex: 1;
    overflow: auto;
    position: relative;
    background: #fff;
  }
  table.matrix-table {
    border-collapse: collapse;
    width: 100%;
    font-size: 12px;
  }
  table.matrix-table th, table.matrix-table td {
    border: 1px solid #e2e8f0;
    padding: 6px 8px;
    text-align: center;
    white-space: nowrap;
  }
  table.matrix-table th {
    background: #f1f5f9;
    color: #475569;
    position: sticky;
    top: 0;
    z-index: 2;
    font-weight: 600;
  }
  table.matrix-table th.remedy-header {
    background: #e0f2fe;
    color: #0369a1;
    font-size: 11px;
    cursor: pointer;
    vertical-align: bottom;
  }
  .remedy-abbrev-v {
    font-weight: 700;
    display: block;
    font-size: 12px;
  }
  table.matrix-table td.rubric-title-cell {
    text-align: left;
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
    background: #f8fafc;
    font-size: 11.5px;
    color: #1e293b;
  }
  .score-cell-4 { background: #fecaca; color: #dc2626; font-weight: bold; }
  .score-cell-3 { background: #bfdbfe; color: #1d4ed8; font-weight: bold; }
  .score-cell-2 { background: #99f6e4; color: #0f766e; font-style: italic; }
  .score-cell-1 { background: #f1f5f9; color: #475569; }

  /* Bottom Details Bar */
  #ro-statusbar {
    background: #1e293b;
    color: #94a3b8;
    padding: 4px 14px;
    font-size: 11.5px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid #334155;
  }
  #ro-statusbar span strong { color: #f1f5f9; }

  /* Modal Dialog for Remedy Details / Materia Medica */
  .modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.5);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 100;
  }
  .modal-content {
    background: #fff;
    width: 600px;
    max-width: 90vw;
    border-radius: 8px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    max-height: 80vh;
  }
  .modal-header {
    background: #2b3e50;
    color: white;
    padding: 12px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .modal-body {
    padding: 18px;
    overflow-y: auto;
    font-size: 13px;
    color: #334155;
    line-height: 1.6;
  }
  .modal-footer {
    padding: 10px 18px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    text-align: right;
  }
</style>
</head>
<body>

<!-- RadarOpus Header -->
<div id="ro-header">
  <div class="ro-menubar">
    <div class="ro-brand">
      <i class="fa-solid fa-compass"></i> RADAR<strong>OPUS</strong> <span>Synthesis Edition 2009V (WinCHIP)</span>
    </div>
    <div style="font-size: 11.5px; color: #cbd5e1;">
      <i class="fa-solid fa-database"></i> Connected: <strong>PostgreSQL (RadarOpus-WinCHIP)</strong> &bull; 180,684 Rubrics &bull; 8,713 Remedies
    </div>
  </div>

  <div class="ro-toolbar">
    <button class="ro-tool-btn active" title="Repertory View"><i class="fa-solid fa-book-medical"></i> Synthesis Repertory</button>
    <button class="ro-tool-btn" id="btn-analysis-toggle" title="Repertorization Grid"><i class="fa-solid fa-chart-simple"></i> Analysis Matrix</button>
    
    <div class="ro-search-container">
      <i class="fa-solid fa-magnifying-glass"></i>
      <input type="text" id="global-search-input" placeholder="Quick Search Rubric (e.g. 'anxiety', 'fear dark', 'head pain morning')... Press Enter" />
    </div>

    <button class="ro-tool-btn" id="btn-export-rep"><i class="fa-solid fa-file-export"></i> Export</button>
    <button class="ro-tool-btn" onclick="clearCurrentClipboard()"><i class="fa-solid fa-trash-can"></i> Clear Clip</button>
  </div>

  <!-- RadarOpus Clipboards -->
  <div class="ro-clipboards-bar">
    <div class="ro-clip-tab active" data-clip="1" onclick="switchClipboard(1)">
      <i class="fa-solid fa-clipboard-list"></i> Clipboard 1 <span class="badge" id="clip-badge-1">0</span>
    </div>
    <div class="ro-clip-tab" data-clip="2" onclick="switchClipboard(2)">
      <i class="fa-solid fa-clipboard-list"></i> Clipboard 2 <span class="badge" id="clip-badge-2">0</span>
    </div>
    <div class="ro-clip-tab" data-clip="3" onclick="switchClipboard(3)">
      <i class="fa-solid fa-clipboard-list"></i> Clipboard 3 <span class="badge" id="clip-badge-3">0</span>
    </div>
    <div class="ro-clip-tab" data-clip="4" onclick="switchClipboard(4)">
      <i class="fa-solid fa-clipboard-list"></i> Clipboard 4 <span class="badge" id="clip-badge-4">0</span>
    </div>
    <div class="ro-clip-tab" data-clip="5" onclick="switchClipboard(5)">
      <i class="fa-solid fa-clipboard-list"></i> Clipboard 5 <span class="badge" id="clip-badge-5">0</span>
    </div>
  </div>
</div>

<!-- 3-Column Main Workspace -->
<div id="ro-main-workspace">
  <!-- Col 1: Chapters Sidebar -->
  <div id="chapters-sidebar">
    <div class="sidebar-title">
      <span>Synthesis Chapters</span>
      <i class="fa-solid fa-list-ol"></i>
    </div>
    <ul id="chapters-list">
      <li style="padding: 16px; text-align: center; color: #94a3b8;">Loading chapters...</li>
    </ul>
  </div>

  <!-- Col 2: Rubric Explorer & Remedies -->
  <div id="rubric-explorer-col">
    <div class="explorer-header">
      <div class="breadcrumb-path" id="current-breadcrumb">
        <i class="fa-regular fa-folder-open"></i> <span id="chapter-name-title">MIND</span> &gt; <strong id="selected-rubric-title">Select a symptom</strong>
      </div>
      <div>
        <button class="btn-sm btn-primary-sm" id="btn-add-active-to-clip" onclick="addCurrentRubricToClip()"><i class="fa-solid fa-plus"></i> Take to Clipboard</button>
      </div>
    </div>

    <!-- Rubrics filter search box -->
    <div id="rubrics-filter-box">
      <input type="text" id="rubrics-filter-input" placeholder="Filter symptoms in this chapter (e.g. anxiety, fear, delirium)..." />
    </div>

    <!-- Rubrics List -->
    <div id="rubrics-list">
      <div style="padding: 24px; text-align: center; color: #94a3b8;">Select a chapter from the left to view rubrics.</div>
    </div>

    <!-- Remedies of Selected Rubric -->
    <div id="rubric-remedies-view">
      <div class="remedies-header-bar">
        <div>
          <i class="fa-solid fa-capsules" style="color: #0284c7;"></i>
          <strong>Remedies in Symptom:</strong> <span id="remedies-count-label">0 remedies</span>
        </div>
        <div class="remedy-filters">
          <label style="font-size: 11px; color: #64748b;">Min Grade:</label>
          <select id="grade-filter" onchange="renderCurrentRemedies()">
            <option value="1">All (Grades 1-4)</option>
            <option value="2">Grade 2+ (Italics & Bold)</option>
            <option value="3">Grade 3+ (Bold & Red)</option>
            <option value="4">Grade 4 Only (Red)</option>
          </select>
          <input type="text" id="remedy-quick-search" placeholder="Filter remedy..." oninput="renderCurrentRemedies()" style="width: 90px;" />
        </div>
      </div>
      <div id="remedies-container">
        <span style="color: #94a3b8; font-style: italic;">Select any rubric above to examine remedy gradings (Red = 4, Bold Blue = 3, Teal Italics = 2, Grey = 1).</span>
      </div>
    </div>
  </div>

  <!-- Col 3: RadarOpus Repertorization Matrix (Dynamic Scoring Sheet) -->
  <div id="repertorization-col">
    <div class="rep-header">
      <h3><i class="fa-solid fa-table-cells" style="color: #0284c7;"></i> Repertorization Sheet</h3>
      <div class="rep-actions">
        <select id="sort-remedy-mode" onchange="recalculateMatrix()" style="font-size: 11px; padding: 3px 6px;">
          <option value="score">Sort by Total Score</option>
          <option value="symptoms">Sort by Symptoms Covered</option>
          <option value="name">Sort by Name</option>
        </select>
      </div>
    </div>

    <div id="matrix-wrapper">
      <table class="matrix-table" id="matrix-table">
        <thead>
          <tr id="matrix-header-row">
            <th style="min-width: 140px; text-align: left;">Symptom (Rubric)</th>
            <th style="width: 40px;">Rem</th>
          </tr>
        </thead>
        <tbody id="matrix-body">
          <tr>
            <td colspan="2" style="padding: 30px; text-align: center; color: #94a3b8;">
              <i class="fa-regular fa-clipboard" style="font-size: 28px; margin-bottom: 8px; display: block;"></i>
              Clipboard is empty.<br>Click <strong>+ Take to Clipboard</strong> on any symptom to repertorize.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<!-- Bottom Status Bar -->
<div id="ro-statusbar">
  <div>
    <span>Synthesis Edition: <strong>Treasure Edition 2009V</strong></span> &bull; 
    <span>Active Clipboard: <strong id="status-active-clip">1</strong></span>
  </div>
  <div>
    <span id="status-info-text">Ready. Double click any remedy for details.</span>
  </div>
</div>

<!-- Remedy Detail Modal -->
<div class="modal-overlay" id="remedy-modal" onclick="closeRemedyModal(event)">
  <div class="modal-content" onclick="event.stopPropagation()">
    <div class="modal-header">
      <h4 id="modal-remedy-name">Remedy Details</h4>
      <i class="fa-solid fa-xmark" style="cursor: pointer;" onclick="closeRemedyModal()"></i>
    </div>
    <div class="modal-body" id="modal-remedy-body">
      Loading remedy information...
    </div>
    <div class="modal-footer">
      <button class="btn-sm" onclick="closeRemedyModal()">Close</button>
    </div>
  </div>
</div>

<script>
  let activeClipboardId = 1;
  let clipboards = { 1: [], 2: [], 3: [], 4: [], 5: [] };
  let currentChapterId = 3; // MIND default
  let currentRubric = null;
  let currentRemediesList = [];

  // Init
  window.addEventListener('DOMContentLoaded', () => {
    loadChapters();
    loadRubricsForChapter(currentChapterId, "MIND");

    // Global search enter
    document.getElementById('global-search-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        performGlobalSearch(e.target.value.trim());
      }
    });

    // Chapter filter
    let filterTimer;
    document.getElementById('rubrics-filter-input').addEventListener('input', (e) => {
      clearTimeout(filterTimer);
      filterTimer = setTimeout(() => {
        loadRubricsForChapter(currentChapterId, null, e.target.value.trim());
      }, 300);
    });
  });

  // Load Chapters (Level 1 in Synthesis 2009)
  async function loadChapters() {
    try {
      const res = await fetch('/api/chapters');
      const chapters = await res.json();
      const list = document.getElementById('chapters-list');
      list.innerHTML = '';
      chapters.forEach((ch, idx) => {
        const li = document.createElement('li');
        li.className = 'chapter-item' + (ch.id === currentChapterId ? ' active' : '');
        li.innerHTML = `<i class="fa-regular fa-bookmark" style="font-size: 11px;"></i> ${ch.name}`;
        li.onclick = () => {
          document.querySelectorAll('.chapter-item').forEach(el => el.classList.remove('active'));
          li.classList.add('active');
          currentChapterId = ch.id;
          document.getElementById('rubrics-filter-input').value = '';
          loadRubricsForChapter(ch.id, ch.name);
        };
        list.appendChild(li);
      });
    } catch (err) {
      console.error("Failed to load chapters", err);
    }
  }

  // Load rubrics for chapter
  async function loadRubricsForChapter(chapterId, chapterName, query = '') {
    if (chapterName) {
      document.getElementById('chapter-name-title').textContent = chapterName;
    }
    const list = document.getElementById('rubrics-list');
    list.innerHTML = '<div style="padding: 16px; text-align: center; color: #94a3b8;">Loading rubrics...</div>';

    try {
      const res = await fetch(`/api/rubrics?chapter_id=${chapterId}&q=${encodeURIComponent(query)}`);
      const rubrics = await res.json();
      list.innerHTML = '';
      if (!rubrics || rubrics.length === 0) {
        list.innerHTML = '<div style="padding: 16px; text-align: center; color: #94a3b8;">No rubrics found.</div>';
        return;
      }

      rubrics.forEach(r => {
        const div = document.createElement('div');
        div.className = 'rubric-row' + (currentRubric && currentRubric.id === r.id ? ' active' : '');
        div.innerHTML = `
          <div class="rubric-text">
            <span>${escapeHtml(r.text)}</span>
          </div>
          <span class="rubric-badge">${r.remedy_count} rem</span>
          <button class="add-to-clip-btn" onclick="event.stopPropagation(); addRubricToClip(${r.id}, '${escapeQuote(r.text)}', ${r.remedy_count})">+ Clip</button>
        `;
        div.onclick = () => {
          document.querySelectorAll('.rubric-row').forEach(el => el.classList.remove('active'));
          div.classList.add('active');
          selectRubric(r);
        };
        list.appendChild(div);
      });

      // Select first rubric by default if none selected
      if (rubrics.length > 0 && !currentRubric) {
        selectRubric(rubrics[0]);
      }
    } catch (err) {
      list.innerHTML = `<div style="padding: 16px; color: red;">Error: ${err.message}</div>`;
    }
  }

  // Select a Rubric and fetch remedies
  async function selectRubric(r) {
    currentRubric = r;
    document.getElementById('selected-rubric-title').textContent = r.text;
    const remediesBox = document.getElementById('remedies-container');
    remediesBox.innerHTML = '<span style="color: #94a3b8;">Loading remedies...</span>';

    try {
      const res = await fetch(`/api/remedies?rubric_id=${r.id}`);
      currentRemediesList = await res.json();
      renderCurrentRemedies();
    } catch (err) {
      remediesBox.innerHTML = `<span style="color: red;">Failed to load remedies: ${err.message}</span>`;
    }
  }

  // Render remedies with Grade styling
  function renderCurrentRemedies() {
    const minGrade = parseInt(document.getElementById('grade-filter').value) || 1;
    const q = (document.getElementById('remedy-quick-search').value || '').toLowerCase().trim();
    const container = document.getElementById('remedies-container');
    container.innerHTML = '';

    const filtered = currentRemediesList.filter(rem => {
      if (rem.degree < minGrade) return false;
      if (q && !rem.abbrev.toLowerCase().includes(q) && !(rem.name || '').toLowerCase().includes(q)) return false;
      return true;
    });

    document.getElementById('remedies-count-label').textContent = `${filtered.length} of ${currentRemediesList.length} remedies`;

    if (filtered.length === 0) {
      container.innerHTML = '<span style="color: #94a3b8; font-style: italic;">No remedies match filter criteria.</span>';
      return;
    }

    filtered.forEach(rem => {
      const span = document.createElement('span');
      span.className = `remedy-tag remedy-grade-${rem.degree}`;
      span.textContent = rem.abbrev;
      span.title = `${rem.name || rem.abbrev} (Grade ${rem.degree})${rem.nosode ? ' [Nosode]' : ''}`;
      span.ondblclick = () => openRemedyModal(rem.id, rem.name, rem.abbrev);
      container.appendChild(span);
    });
  }

  // Global Search across entire Synthesis 2009 (180k rubrics)
  async function performGlobalSearch(query) {
    if (!query) return;
    const list = document.getElementById('rubrics-list');
    document.getElementById('chapter-name-title').textContent = `Search: "${query}"`;
    document.getElementById('selected-rubric-title').textContent = "Select result";
    list.innerHTML = '<div style="padding: 16px; text-align: center; color: #94a3b8;">Searching entire Synthesis Repertory...</div>';

    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      const rubrics = await res.json();
      list.innerHTML = '';
      if (!rubrics || rubrics.length === 0) {
        list.innerHTML = `<div style="padding: 16px; text-align: center; color: #94a3b8;">No rubrics found matching "${query}".</div>`;
        return;
      }
      rubrics.forEach(r => {
        const div = document.createElement('div');
        div.className = 'rubric-row';
        div.innerHTML = `
          <div class="rubric-text">
            <span style="font-size: 11px; color: #0284c7; font-weight: bold; margin-right: 6px;">[${r.chapter || 'SYNTHESIS'}]</span>
            <span>${escapeHtml(r.text)}</span>
          </div>
          <span class="rubric-badge">${r.remedy_count} rem</span>
          <button class="add-to-clip-btn" onclick="event.stopPropagation(); addRubricToClip(${r.id}, '${escapeQuote(r.text)}', ${r.remedy_count})">+ Clip</button>
        `;
        div.onclick = () => {
          document.querySelectorAll('.rubric-row').forEach(el => el.classList.remove('active'));
          div.classList.add('active');
          selectRubric(r);
        };
        list.appendChild(div);
      });
      if (rubrics.length > 0) selectRubric(rubrics[0]);
    } catch (err) {
      list.innerHTML = `<div style="padding: 16px; color: red;">Error: ${err.message}</div>`;
    }
  }

  // Clipboards Handling
  function switchClipboard(clipNum) {
    activeClipboardId = clipNum;
    document.querySelectorAll('.ro-clip-tab').forEach(el => {
      el.classList.toggle('active', parseInt(el.getAttribute('data-clip')) === clipNum);
    });
    document.getElementById('status-active-clip').textContent = clipNum;
    recalculateMatrix();
  }

  function addCurrentRubricToClip() {
    if (!currentRubric) return;
    addRubricToClip(currentRubric.id, currentRubric.text, currentRubric.remedy_count || currentRemediesList.length);
  }

  async function addRubricToClip(rubricId, text, remedyCount) {
    const clip = clipboards[activeClipboardId];
    if (clip.some(item => item.id === rubricId)) {
      alert("This symptom is already in the active clipboard.");
      return;
    }

    // Fetch remedies for scoring
    const res = await fetch(`/api/remedies?rubric_id=${rubricId}`);
    const remedies = await res.json();

    clip.push({
      id: rubricId,
      text: text,
      remedy_count: remedyCount,
      remedies: remedies
    });

    document.getElementById(`clip-badge-${activeClipboardId}`).textContent = clip.length;
    recalculateMatrix();
  }

  function clearCurrentClipboard() {
    if (confirm(`Clear all symptoms from Clipboard ${activeClipboardId}?`)) {
      clipboards[activeClipboardId] = [];
      document.getElementById(`clip-badge-${activeClipboardId}`).textContent = '0';
      recalculateMatrix();
    }
  }

  // Repertorization Calculation & Matrix Render
  function recalculateMatrix() {
    const clip = clipboards[activeClipboardId];
    const headerRow = document.getElementById('matrix-header-row');
    const tbody = document.getElementById('matrix-body');

    if (!clip || clip.length === 0) {
      headerRow.innerHTML = '<th style="min-width: 140px; text-align: left;">Symptom (Rubric)</th><th style="width: 40px;">Rem</th>';
      tbody.innerHTML = `
        <tr>
          <td colspan="2" style="padding: 30px; text-align: center; color: #94a3b8;">
            <i class="fa-regular fa-clipboard" style="font-size: 28px; margin-bottom: 8px; display: block;"></i>
            Clipboard ${activeClipboardId} is empty.<br>Click <strong>+ Take to Clipboard</strong> on any symptom to repertorize.
          </td>
        </tr>
      `;
      return;
    }

    // Aggregate remedies
    const remedyStats = {}; // { abbrev: { id, name, totalScore, symptomsCovered, grades: { rubricId: degree } } }

    clip.forEach(rubric => {
      rubric.remedies.forEach(rem => {
        if (!remedyStats[rem.abbrev]) {
          remedyStats[rem.abbrev] = {
            id: rem.id,
            abbrev: rem.abbrev,
            name: rem.name,
            totalScore: 0,
            symptomsCovered: 0,
            grades: {}
          };
        }
        remedyStats[rem.abbrev].totalScore += rem.degree;
        remedyStats[rem.abbrev].symptomsCovered += 1;
        remedyStats[rem.abbrev].grades[rubric.id] = rem.degree;
      });
    });

    const sortMode = document.getElementById('sort-remedy-mode').value;
    let sortedRemedies = Object.values(remedyStats);
    if (sortMode === 'score') {
      sortedRemedies.sort((a, b) => b.totalScore - a.totalScore || b.symptomsCovered - a.symptomsCovered);
    } else if (sortMode === 'symptoms') {
      sortedRemedies.sort((a, b) => b.symptomsCovered - a.symptomsCovered || b.totalScore - a.totalScore);
    } else {
      sortedRemedies.sort((a, b) => a.abbrev.localeCompare(b.abbrev));
    }

    // Top 20 remedies for display width
    const displayRemedies = sortedRemedies.slice(0, 20);

    // Build Header
    let hHtml = '<th style="min-width: 150px; text-align: left;">Symptom (Rubric)</th><th style="width: 35px;">Rem</th>';
    displayRemedies.forEach(r => {
      hHtml += `
        <th class="remedy-header" title="${r.name || r.abbrev}" onclick="openRemedyModal(${r.id}, '${escapeQuote(r.name)}', '${escapeQuote(r.abbrev)}')">
          <span class="remedy-abbrev-v">${r.abbrev}</span>
          <span style="font-size: 10px; color: #64748b;">${r.symptomsCovered}/${r.totalScore}</span>
        </th>
      `;
    });
    headerRow.innerHTML = hHtml;

    // Summary Rows (Symptoms Count & Total Points)
    let bHtml = '';
    
    // Row 1: Symptoms Covered Count
    bHtml += '<tr style="background: #e2e8f0; font-weight: bold;"><td class="rubric-title-cell"><strong>Total Symptoms Covered</strong></td><td>-</td>';
    displayRemedies.forEach(r => {
      bHtml += `<td style="color: #0369a1; font-weight: 700;">${r.symptomsCovered}</td>`;
    });
    bHtml += '</tr>';

    // Row 2: Total Degrees Sum
    bHtml += '<tr style="background: #f1f5f9; font-weight: bold;"><td class="rubric-title-cell"><strong>Sum of Degrees (Points)</strong></td><td>-</td>';
    displayRemedies.forEach(r => {
      bHtml += `<td style="color: #dc2626; font-weight: 700;">${r.totalScore}</td>`;
    });
    bHtml += '</tr>';

    // Rubric Rows
    clip.forEach(rubric => {
      bHtml += `<tr>
        <td class="rubric-title-cell" title="${escapeHtml(rubric.text)}">
          <i class="fa-solid fa-xmark" style="color: #ef4444; cursor: pointer; margin-right: 6px;" title="Remove symptom" onclick="removeRubricFromClip(${rubric.id})"></i>
          ${escapeHtml(rubric.text)}
        </td>
        <td style="font-size: 10px; color: #64748b;">${rubric.remedy_count}</td>
      `;

      displayRemedies.forEach(r => {
        const grade = r.grades[rubric.id];
        if (grade) {
          bHtml += `<td class="score-cell-${grade}">${grade}</td>`;
        } else {
          bHtml += '<td style="color: #cbd5e1;">-</td>';
        }
      });
      bHtml += '</tr>';
    });

    tbody.innerHTML = bHtml;
  }

  function removeRubricFromClip(rubricId) {
    clipboards[activeClipboardId] = clipboards[activeClipboardId].filter(r => r.id !== rubricId);
    document.getElementById(`clip-badge-${activeClipboardId}`).textContent = clipboards[activeClipboardId].length;
    recalculateMatrix();
  }

  // Remedy Modal Dialog
  async function openRemedyModal(remedyId, remedyName, remedyAbbrev) {
    const modal = document.getElementById('remedy-modal');
    const title = document.getElementById('modal-remedy-name');
    const body = document.getElementById('modal-remedy-body');
    title.innerHTML = `<i class="fa-solid fa-capsules"></i> ${remedyName || remedyAbbrev} (${remedyAbbrev})`;
    body.innerHTML = 'Loading remedy passport & botanical information...';
    modal.style.display = 'flex';

    try {
      const res = await fetch(`/api/remedy_details?id=${remedyId}`);
      const data = await res.json();
      body.innerHTML = `
        <div style="margin-bottom: 12px;"><strong>Abbreviation:</strong> ${data.abbrev || '-'}</div>
        <div style="margin-bottom: 12px;"><strong>Full Name:</strong> ${data.name || '-'}</div>
        <div style="margin-bottom: 12px;"><strong>Scientific / Botanical Name:</strong> ${data.scientific_name || '-'}</div>
        <div style="margin-bottom: 12px;"><strong>Common Names:</strong> ${data.common_names || '-'}</div>
        <div style="margin-bottom: 12px;"><strong>Origin / Kingdom:</strong> ${data.origin || 'Standard Homeopathic Provings'}</div>
        <div style="margin-bottom: 12px;"><strong>Is Nosode:</strong> ${data.nosode ? 'Yes' : 'No'}</div>
        <div style="margin-bottom: 12px;"><strong>Synthesis Frequency:</strong> ${data.frequency || 0} rubrics in Synthesis</div>
        <div style="margin-top: 16px; padding: 12px; background: #f1f5f9; border-radius: 6px; font-size: 12px;">
          <strong>Research Info:</strong><br>
          ${data.research_info || 'No external research notes attached in WinCHIP.'}
        </div>
      `;
    } catch (err) {
      body.innerHTML = `<span style="color: red;">Failed to load remedy details: ${err.message}</span>`;
    }
  }

  function closeRemedyModal(event) {
    document.getElementById('remedy-modal').style.display = 'none';
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function escapeQuote(str) {
    if (!str) return '';
    return str.replace(/'/g, "\\'");
  }
</script>
</body>
</html>
"""

class RadarOpusHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))

        elif path == "/api/chapters":
            # Level 1 rubrics in Synthesis 2009 (MIND, VERTIGO, HEAD, etc.)
            sql = '''
            SELECT DISTINCT dro.dro_documentrecordid as id, dro.dro_order as ord, drt.drt_text as name
            FROM "_000000002".documentrecordorder dro
            JOIN "_000000002".documentrecordtext drt ON dro.dro_documentrecordid = drt.drt_documentrecordid
            WHERE drt.drt_documentdescriptionid = 2 AND dro.dro_parentid = 1
            ORDER BY dro.dro_order;
            '''
            try:
                rows = run_query_json(sql)
                self.send_json(rows)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        elif path == "/api/rubrics":
            chapter_id = qs.get("chapter_id", ["3"])[0]
            q = qs.get("q", [""])[0].strip()
            
            if q:
                sql = f'''
                SELECT dro.dro_documentrecordid as id, drt.drt_text as text,
                       (SELECT count(*) FROM "_000000002".hom_addition ha WHERE ha.ra_rubricid = dro.dro_documentrecordid) as remedy_count
                FROM "_000000002".documentrecordorder dro
                JOIN "_000000002".documentrecordtext drt ON dro.dro_documentrecordid = drt.drt_documentrecordid
                WHERE drt.drt_documentdescriptionid = 2 AND dro.dro_parentid = {chapter_id}
                  AND drt.drt_text ILIKE '%{q}%'
                ORDER BY dro.dro_order
                LIMIT 80;
                '''
            else:
                sql = f'''
                SELECT dro.dro_documentrecordid as id, drt.drt_text as text,
                       (SELECT count(*) FROM "_000000002".hom_addition ha WHERE ha.ra_rubricid = dro.dro_documentrecordid) as remedy_count
                FROM "_000000002".documentrecordorder dro
                JOIN "_000000002".documentrecordtext drt ON dro.dro_documentrecordid = drt.drt_documentrecordid
                WHERE drt.drt_documentdescriptionid = 2 AND dro.dro_parentid = {chapter_id}
                ORDER BY dro.dro_order
                LIMIT 80;
                '''
            try:
                rows = run_query_json(sql)
                self.send_json(rows)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        elif path == "/api/search":
            q = qs.get("q", [""])[0].strip()
            if not q:
                self.send_json([])
                return
            words = q.split()
            where_clauses = " AND ".join([f"drt.drt_text ILIKE '%{w}%'" for w in words])
            sql = f'''
            SELECT dro.dro_documentrecordid as id, drt.drt_text as text,
                   (SELECT count(*) FROM "_000000002".hom_addition ha WHERE ha.ra_rubricid = dro.dro_documentrecordid) as remedy_count
            FROM "_000000002".documentrecordorder dro
            JOIN "_000000002".documentrecordtext drt ON dro.dro_documentrecordid = drt.drt_documentrecordid
            WHERE drt.drt_documentdescriptionid = 2 AND {where_clauses}
            LIMIT 100;
            '''
            try:
                rows = run_query_json(sql)
                self.send_json(rows)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        elif path == "/api/remedies":
            rubric_id = qs.get("rubric_id", [""])[0]
            if not rubric_id:
                self.send_json([])
                return
            sql = f'''
            SELECT ha.ra_objectid as id, ha.ra_degree as degree, hr.r_abbrev as abbrev, hr.r_name as name, hr.r_nosode as nosode
            FROM "_000000002".hom_addition ha
            JOIN homeo.hom_remedy hr ON ha.ra_objectid = hr.r_id
            WHERE ha.ra_rubricid = {rubric_id}
            ORDER BY ha.ra_degree DESC, hr.r_abbrev ASC;
            '''
            try:
                rows = run_query_json(sql)
                self.send_json(rows)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        elif path == "/api/remedy_details":
            remedy_id = qs.get("id", [""])[0]
            if not remedy_id:
                self.send_json({})
                return
            sql = f'''
            SELECT r_id as id, r_abbrev as abbrev, r_name as name, r_origin as origin,
                   r_frequence as frequency, r_scientificname as scientific_name,
                   r_nosode as nosode, r_commonnames as common_names, r_researchinfo as research_info
            FROM homeo.hom_remedy
            WHERE r_id = {remedy_id}
            LIMIT 1;
            '''
            try:
                rows = run_query_json(sql)
                self.send_json(rows[0] if rows else {})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        else:
            self.send_error(404)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

def main():
    server = HTTPServer(("127.0.0.1", PORT), RadarOpusHandler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"======================================================")
    print(f" RadarOpus Web UI Server running at {url}")
    print(f" Connected to PostgreSQL (RadarOpus-WinCHIP)")
    print(f"======================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping RadarOpus Web UI server...")

if __name__ == "__main__":
    main()
