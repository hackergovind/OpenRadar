import re
import os
import sys

base_dir = r"L:\Project\OpenRadar"
app_py = os.path.join(base_dir, "radaropus_app.py")
out_html = os.path.join(base_dir, "android", "app", "src", "main", "assets", "index.html")

with open(app_py, "r", encoding="utf-8") as f:
    content = f.read()

# Extract HTML_PAGE
m = re.search(r'HTML_PAGE = """(.*?)"""', content, re.DOTALL)
if not m:
    print("Failed to find HTML_PAGE")
    sys.exit(1)

html = m.group(1)

android_api_bridge = """
  const isAndroid = (typeof window.Android !== 'undefined');

  async function apiGet(endpoint, params = {}) {
    if (isAndroid) {
      if (endpoint === '/api/chapters') {
        return JSON.parse(window.Android.getChapters());
      } else if (endpoint === '/api/rubrics') {
        return JSON.parse(window.Android.getRubrics(parseInt(params.parent_id || 3), params.q || ''));
      } else if (endpoint === '/api/search') {
        return JSON.parse(window.Android.searchRubrics(params.q || ''));
      } else if (endpoint === '/api/remedies') {
        return JSON.parse(window.Android.getRemedies(parseInt(params.rubric_id || 0)));
      } else if (endpoint === '/api/remedy_details') {
        return JSON.parse(window.Android.getRemedyDetails(parseInt(params.id || 0)));
      }
    }
    const qs = new URLSearchParams(params).toString();
    const url = qs ? `${endpoint}?${qs}` : endpoint;
    const res = await fetch(url);
    return await res.json();
  }
"""

html = html.replace("const res = await fetch('/api/chapters');\n      const chapters = await res.json();", "const chapters = await apiGet('/api/chapters');")
html = html.replace("const res = await fetch(`/api/rubrics?parent_id=${parentId}&q=${encodeURIComponent(q)}`);\n      const rubrics = await res.json();", "const rubrics = await apiGet('/api/rubrics', { parent_id: parentId, q: q });")
html = html.replace("const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);\n      const rubrics = await res.json();", "const rubrics = await apiGet('/api/search', { q: q });")
html = html.replace("const res = await fetch(`/api/remedies?rubric_id=${rubric.id}`);\n      const remedies = await res.json();", "const remedies = await apiGet('/api/remedies', { rubric_id: rubric.id });")
html = html.replace("const res = await fetch(`/api/remedies?rubric_id=${rubricId}`);\n        const remedies = await res.json();", "const remedies = await apiGet('/api/remedies', { rubric_id: rubricId });")
html = html.replace("const res = await fetch(`/api/remedy_details?id=${remedyId}`);\n      const data = await res.json();", "const data = await apiGet('/api/remedy_details', { id: remedyId });")

html = html.replace("<script>", "<script>\n" + android_api_bridge)

mobile_css = """
<style>
  @media (max-width: 900px) {
    #ro-body { flex-direction: column !important; }
    #col-chapters { display: none; width: 100% !important; height: calc(100vh - 120px); }
    #col-rubrics { width: 100% !important; flex: 1; }
    #col-matrix { display: none; width: 100% !important; height: calc(100vh - 120px); }
    
    .mobile-tab-bar {
      display: flex !important;
      background: #0f172a;
      border-top: 1px solid #334155;
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: 52px;
      z-index: 1000;
    }
    .mobile-tab-btn {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: #94a3b8;
      font-size: 10px;
      gap: 3px;
      background: transparent;
      border: none;
      cursor: pointer;
    }
    .mobile-tab-btn.active {
      color: #38bdf8;
      font-weight: bold;
    }
    .mobile-tab-btn i { font-size: 16px; }
    body { padding-bottom: 52px; }
  }
  .mobile-tab-bar { display: none; }
</style>
"""

html = html.replace("</head>", mobile_css + "\n</head>")

mobile_html = """
<div class="mobile-tab-bar">
  <button class="mobile-tab-btn active" id="btn-tab-rubrics" onclick="switchMobileTab('rubrics')">
    <i class="fa-solid fa-book-medical"></i> Rubrics
  </button>
  <button class="mobile-tab-btn" id="btn-tab-chapters" onclick="switchMobileTab('chapters')">
    <i class="fa-solid fa-list"></i> Chapters
  </button>
  <button class="mobile-tab-btn" id="btn-tab-matrix" onclick="switchMobileTab('matrix')">
    <i class="fa-solid fa-chart-column"></i> Analysis
  </button>
</div>

<script>
  function switchMobileTab(tab) {
    document.querySelectorAll('.mobile-tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('btn-tab-' + tab).classList.add('active');
    
    const colChap = document.getElementById('col-chapters');
    const colRub = document.getElementById('col-rubrics');
    const colMat = document.getElementById('col-matrix');
    
    if (tab === 'rubrics') {
      colChap.style.display = 'none';
      colRub.style.display = 'flex';
      colMat.style.display = 'none';
    } else if (tab === 'chapters') {
      colChap.style.display = 'flex';
      colRub.style.display = 'none';
      colMat.style.display = 'none';
    } else if (tab === 'matrix') {
      colChap.style.display = 'none';
      colRub.style.display = 'none';
      colMat.style.display = 'flex';
      recalculateMatrix();
    }
  }
  
  const origNav = navigateToNode;
  navigateToNode = function(id, name, isChap) {
    origNav(id, name, isChap);
    if (window.innerWidth <= 900) {
      switchMobileTab('rubrics');
    }
  };
</script>
"""

html = html.replace("</body>", mobile_html + "\n</body>")

with open(out_html, "w", encoding="utf-8") as f:
    f.write(html)

print("Generated:", out_html)
