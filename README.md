# OpenRadar 🧭

**OpenRadar** is an open-source, modern web-based medical repertorization and homeopathic practice management platform inspired by **RadarOpus** (Synthesis Repertory & WinCHIP).

It connects directly to the underlying PostgreSQL clinical database containing the complete **Synthesis Treasure Edition Repertory (180,684 Rubrics, 1,157,340 Symptom-Remedy additions, and 8,713 Remedies)**.

---

## 🌟 Key Features

* **3-Column Classical Repertory Workspace:**
  * **Synthesis Chapters (42 Chapters):** From `MIND`, `VERTIGO`, `HEAD`, `STOMACH`, `CHEST` to `GENERALS`.
  * **Hierarchical Rubric Explorer:** Search symptoms with live counts of remedy coverage.
  * **Remedy Grading Engine:** Authentic 4-grade homeopathic distinction:
    * **Grade 4 (Bold Red Underlined):** Highest clinical verification
    * **Grade 3 (Bold Blue):** Prominent remedy
    * **Grade 2 (Italics Teal):** Verified symptom
    * **Grade 1 (Grey):** Observed symptom
  * **Interactive Repertorization Sheet (Grid):** Real-time matrix calculation of:
    * Total Symptoms Covered
    * Sum of Degrees (Points)
    * Instant sorting by Total Score, Symptoms Covered, or Alphabetical.
* **Multi-Clipboard System:**
  * 5 Clipboards for separating Generals, Causation, Particulars, and Mental rubrics.
* **Global Repertory Search:**
  * Ultra-fast multi-word search across all 1.8 Lakh rubrics.
* **Remedy Passport & Materia Medica Card:**
  * Double-click any remedy to view Botanical/Scientific name, Common names, Nosode classification, and provings research.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.8+
* PostgreSQL with RadarOpus / WinCHIP schema loaded

### Running the App
1. Run the launcher script:
```bash
launch_radaropus_ui.bat
```
2. Or start directly via Python:
```bash
python radaropus_app.py
```
3. Open your browser and navigate to:
```
http://127.0.0.1:8080
```

---

## 🛠 Tech Architecture
* **Frontend:** Clean Single Page Application (SPA) responsive interface with FontAwesome icons and zero heavy external build dependencies.
* **Backend:** Native Python HTTP server interface with optimized PostgreSQL queries (`json_agg`).
* **Database:** PostgreSQL (`RadarOpus-WinCHIP`).

---

## 📄 License
MIT License. Created with ❤️ for homeopathic practitioners and researchers.
