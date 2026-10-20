import os
import sys
import sqlite3
import subprocess
import time

PG_BIN = r"L:\Project\PostgreSQL\bin\psql.exe"
PG_HOST = "127.0.0.1"
PG_PORT = "5434"
PG_USER = "postgres"
PG_PASS = "admin123"
PG_DB = "RadarOpus-WinCHIP"

SQLITE_PATH = r"L:\Project\OpenRadar\openradar.db"

def run_psql_csv(sql, out_csv_path):
    env = os.environ.copy()
    env["PGPASSWORD"] = PG_PASS
    # Replace newlines in research notes to prevent CSV row splits
    copy_cmd = f"\\copy ({sql.strip().rstrip(';')}) TO '{out_csv_path}' WITH (FORMAT csv, HEADER false, QUOTE '\"', ESCAPE '\\');"
    cmd = [
        PG_BIN,
        "-h", PG_HOST,
        "-p", PG_PORT,
        "-U", PG_USER,
        "-d", PG_DB,
        "-c", copy_cmd
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        raise Exception(f"Query failed: {res.stderr}")

def main():
    start_time = time.time()
    print("==============================================================")
    print(" Exporting Core English Synthesis to Lightweight SQLite DB ")
    print("==============================================================")
    
    if os.path.exists(SQLITE_PATH):
        try:
            os.remove(SQLITE_PATH)
        except Exception:
            pass

    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA synchronous = OFF;")
    cursor.execute("PRAGMA journal_mode = MEMORY;")

    tmp_dir = r"L:\Project\OpenRadar\tmp_export"
    os.makedirs(tmp_dir, exist_ok=True)

    # 1. Remedies Table
    print("\n[1/4] Exporting Remedies (8,713 remedies)...")
    cursor.execute("""
    CREATE TABLE remedies (
        id INTEGER PRIMARY KEY,
        abbrev TEXT,
        name TEXT,
        scientific_name TEXT,
        common_names TEXT,
        origin TEXT,
        is_nosode INTEGER,
        frequency INTEGER,
        research_info TEXT
    );
    """)
    conn.commit()

    rem_sql = """
    SELECT r_id, 
           COALESCE(r_abbrev, ''), 
           COALESCE(r_name, ''), 
           COALESCE(r_scientificname, ''), 
           COALESCE(r_commonnames, ''), 
           COALESCE(r_origin, ''),
           CASE WHEN r_nosode THEN 1 ELSE 0 END,
           COALESCE(r_frequence, 0),
           REPLACE(REPLACE(COALESCE(r_researchinfo, ''), E'\\n', ' '), E'\\r', ' ')
    FROM homeo.hom_remedy;
    """
    rem_csv = os.path.join(tmp_dir, "remedies.csv")
    run_psql_csv(rem_sql, rem_csv)

    import csv
    with open(rem_csv, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        batch = []
        for r in reader:
            if len(r) == 9:
                batch.append(r)
            elif len(r) > 9:
                batch.append(r[:8] + [" ".join(r[8:])])
        cursor.executemany("INSERT INTO remedies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", batch)
    conn.commit()
    print(f" -> {cursor.execute('SELECT count(*) FROM remedies;').fetchone()[0]} Remedies imported.")

    # 2. Chapters Table (41 Classical Chapters)
    print("\n[2/4] Exporting Synthesis Chapters...")
    cursor.execute("""
    CREATE TABLE chapters (
        id INTEGER PRIMARY KEY,
        order_idx INTEGER,
        name TEXT
    );
    """)
    conn.commit()

    chap_sql = """
    SELECT dro.dro_documentrecordid, dro.dro_order, drt.drt_text
    FROM "_000000002".documentrecordorder dro
    JOIN "_000000002".documentrecordtext drt 
      ON dro.dro_documentrecordid = drt.drt_documentrecordid
     AND drt.drt_documentdescriptionid = 2
    WHERE dro.dro_documentsortingid = 2 AND dro.dro_parentid = 1
    ORDER BY dro.dro_order;
    """
    chap_csv = os.path.join(tmp_dir, "chapters.csv")
    run_psql_csv(chap_sql, chap_csv)

    with open(chap_csv, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        cursor.executemany("INSERT INTO chapters VALUES (?, ?, ?);", reader)
    conn.commit()
    print(f" -> {cursor.execute('SELECT count(*) FROM chapters;').fetchone()[0]} Chapters imported.")

    # 3. Rubrics Table
    print("\n[3/4] Exporting English Rubrics (Hierarchy & Text)...")
    cursor.execute("""
    CREATE TABLE rubrics (
        id INTEGER PRIMARY KEY,
        parent_id INTEGER,
        level INTEGER,
        order_idx INTEGER,
        suborder_idx INTEGER,
        has_child INTEGER,
        text TEXT,
        parent_path TEXT,
        full_path TEXT
    );
    """)
    conn.commit()

    rubrics_sql = """
    SELECT dro.dro_documentrecordid,
           dro.dro_parentid,
           dro.dro_level,
           dro.dro_order,
           dro.dro_suborder,
           COALESCE(dro.dro_havechild, 0),
           REPLACE(REPLACE(COALESCE(drt.drt_text, ''), E'\\n', ' '), E'\\r', ' '),
           REPLACE(REPLACE(COALESCE(pdrt.drt_text, ''), E'\\n', ' '), E'\\r', ' '),
           CASE 
               WHEN pdrt.drt_text IS NOT NULL AND pdrt.drt_text != '' THEN pdrt.drt_text || ' > ' || drt.drt_text
               ELSE drt.drt_text
           END
    FROM "_000000002".documentrecordorder dro
    JOIN "_000000002".documentrecordtext drt 
      ON dro.dro_documentrecordid = drt.drt_documentrecordid 
     AND drt.drt_documentdescriptionid = 2
    LEFT JOIN "_000000002".documentrecordtext pdrt
      ON dro.dro_parentid = pdrt.drt_documentrecordid
     AND pdrt.drt_documentdescriptionid = 2
    WHERE dro.dro_documentsortingid = 2;
    """
    rubrics_csv = os.path.join(tmp_dir, "rubrics.csv")
    run_psql_csv(rubrics_sql, rubrics_csv)

    with open(rubrics_csv, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        cursor.executemany("INSERT INTO rubrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", reader)
    conn.commit()
    print(f" -> {cursor.execute('SELECT count(*) FROM rubrics;').fetchone()[0]} Rubrics imported.")

    # 4. Rubric Additions (Remedies & Grades)
    print("\n[4/4] Exporting Symptom-Remedy Additions (1.15 Million links)...")
    cursor.execute("""
    CREATE TABLE rubric_remedies (
        rubric_id INTEGER,
        remedy_id INTEGER,
        degree INTEGER
    );
    """)
    conn.commit()

    add_sql = """
    SELECT ra_rubricid, ra_objectid, ra_degree
    FROM "_000000002".hom_addition
    WHERE ra_degree > 0;
    """
    add_csv = os.path.join(tmp_dir, "additions.csv")
    run_psql_csv(add_sql, add_csv)

    with open(add_csv, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        cursor.executemany("INSERT INTO rubric_remedies VALUES (?, ?, ?);", reader)
    conn.commit()
    print(f" -> {cursor.execute('SELECT count(*) FROM rubric_remedies;').fetchone()[0]} Symptom-Remedy links imported.")

    # Precalculate remedy count for each rubric
    print("\n[Optimization] Precalculating remedy counts per rubric...")
    cursor.execute("ALTER TABLE rubrics ADD COLUMN remedy_count INTEGER DEFAULT 0;")
    cursor.execute("""
    CREATE TEMP TABLE tmp_counts AS 
    SELECT rubric_id, count(*) as cnt 
    FROM rubric_remedies 
    GROUP BY rubric_id;
    """)
    cursor.execute("""
    UPDATE rubrics 
    SET remedy_count = COALESCE((SELECT cnt FROM tmp_counts WHERE tmp_counts.rubric_id = rubrics.id), 0);
    """)
    cursor.execute("DROP TABLE tmp_counts;")
    conn.commit()

    # Create Indexes for lightning fast queries
    print("\n[Optimization] Building High-Speed SQLite B-Tree Indexes...")
    cursor.execute("CREATE INDEX idx_rubrics_parent ON rubrics (parent_id);")
    cursor.execute("CREATE INDEX idx_rubrics_text ON rubrics (text);")
    cursor.execute("CREATE INDEX idx_rubrics_full_path ON rubrics (full_path);")
    cursor.execute("CREATE INDEX idx_rr_rubric ON rubric_remedies (rubric_id, degree DESC);")
    cursor.execute("CREATE INDEX idx_rr_remedy ON rubric_remedies (remedy_id);")
    cursor.execute("CREATE INDEX idx_remedies_abbrev ON remedies (abbrev);")
    cursor.execute("CREATE INDEX idx_remedies_name ON remedies (name);")
    conn.commit()

    # VACUUM to shrink database
    print("\n[Optimization] Running VACUUM to compress database...")
    cursor.execute("VACUUM;")
    conn.close()

    # Clean up temp CSVs
    for f in [rem_csv, chap_csv, rubrics_csv, add_csv]:
        if os.path.exists(f):
            os.remove(f)
    try:
        os.rmdir(tmp_dir)
    except Exception:
        pass

    size_mb = os.path.getsize(SQLITE_PATH) / (1024 * 1024)
    elapsed = time.time() - start_time
    print(f"\n==============================================================")
    print(f" SUCCESS: openradar.db generated in {elapsed:.1f} seconds!")
    print(f" Final SQLite File Size: {size_mb:.2f} MB")
    print(f" Location: {SQLITE_PATH}")
    print(f"==============================================================")

if __name__ == "__main__":
    main()
