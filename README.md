# OpenRadar 🧭
> **Open-Source RadarOpus Alternative: Modern Synthesis Repertory & Practice Management**

**OpenRadar** is a blazing-fast, lightweight, open-source medical repertorization platform inspired by **RadarOpus** (Synthesis Repertory & WinCHIP).

It contains the complete **Synthesis Treasure Edition 2009V Repertory**:
- 📚 **180,683 Classical Rubrics** across all 41 chapters (`MIND`, `VERTIGO`, `HEAD`, `STOMACH`, `GENERALS`, etc.)
- 💊 **8,713 Remedies** with botanical names, common names, nosode status, and frequency
- 🔬 **1,157,340 Symptom-Remedy Additions** with 4-degree clinical gradings
- 📷 **1,026+ Botanical HD Photos & Clinician Audio Lectures** (Frederik Schroyens, Farokh Master, etc.)

---

## ⚡ Zero-Dependency SQLite Engine (Only 68 MB!)

Originally stored in a **14.5 GB** PostgreSQL database, the core English clinical dataset has been extracted and indexed into a **68.5 MB SQLite database (`openradar.db`)**.

- **Instant Sub-20ms Queries:** B-Tree indexed search across 180,000+ rubrics.
- **Zero External Dependencies:** Built with Python standard library (`sqlite3`, `http.server`). No pip packages required.
- **Offline & Cloud Ready:** Runs anywhere from a laptop to free cloud hosting.

---

## 🌟 Key Features

* **Classical 3-Column Repertory Workspace:**
  * **Synthesis Chapters (41 Chapters):** Instant navigation through classical chapters.
  * **Hierarchical Rubric Explorer:** Sub-rubric tree navigation with live remedy counts.
  * **Classical 4-Grade Remedy Styling:**
    * **Grade 4 (Bold Red Underlined):** Highest clinical verification
    * **Grade 3 (Bold Blue):** Prominent remedy
    * **Grade 2 (Italics Teal):** Verified symptom
    * **Grade 1 (Grey):** Observed symptom
* **Repertorization Matrix Sheet:**
  * Real-time calculation of **Symptoms Covered** and **Sum of Degrees (Points)**.
  * Sortable by Score, Symptoms Covered, or Alphabetical.
  * One-click PDF / Print export for clinical records.
* **5 Multi-Clipboards:**
  * Organize rubrics across Mental, Causation, Generals, Modalities, and Particulars.
* **Smart Medical Search:**
  * Maps natural language complaints (e.g., `"headache"`) directly to repertory equivalents (`HEAD > PAIN`).
* **Remedy Passport & Multimedia:**
  * Botanical/scientific classification, provings research notes, and substance photos.

---

## 🚀 Quick Start (Local)

No database installation required!

```bash
# Clone the repository
git clone https://github.com/hackergovind/OpenRadar.git
cd OpenRadar

# Run the app (Windows)
launch_radaropus_ui.bat

# Or run with Python directly (Windows / Mac / Linux)
python radaropus_app.py
```

Then open your browser at **`http://localhost:8080`**.

---

## 🌐 100% Free Cloud Hosting Guide

Because `openradar.db` is only 68.5 MB, you can host the entire web app and database for **free** on multiple platforms:

### Option 1: Render.com (Recommended - 1 Click)
1. Fork or push this repository to your GitHub account.
2. Sign in to [Render.com](https://render.com) (Free account, no credit card required).
3. Click **New +** → **Web Service** → Connect your `OpenRadar` GitHub repository.
4. Set settings:
   - **Environment:** `Python 3`
   - **Build Command:** *(leave blank)*
   - **Start Command:** `python radaropus_app.py`
5. Click **Create Web Service**. Your app is live with a free HTTPS domain!

### Option 2: Koyeb / Fly.io / Railway
This repo includes a `Dockerfile` and `Procfile`. Simply link your GitHub repo to deploy on any Docker/container PaaS.

### Option 3: Turso Cloud (LibSQL / SQLite Edge)
If you want serverless edge database hosting:
```bash
turso db create openradar --from-file openradar.db
```
Turso provides 9 GB free storage (OpenRadar uses < 1% of the free quota).

---

## 📁 Repository Structure

```
OpenRadar/
├── openradar.db          # 68.5 MB Complete Synthesis 2009 Repertory & Remedies
├── radaropus_app.py      # High-performance web server & RadarOpus UI
├── export_to_sqlite.py   # ETL pipeline script (PostgreSQL -> SQLite)
├── launch_radaropus_ui.bat # 1-click Windows launcher
├── Dockerfile            # Container deployment configuration
├── Procfile              # PaaS process file (Render / Railway / Heroku)
└── README.md             # Documentation & Setup Guide
```

---

## 📄 License
MIT License. Created with ❤️ for homeopathic practitioners, researchers, and students.
