"""
TecoQC - Persistencia SQLite de resultados de inspección
"""

import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.expanduser("~"), ".tecoqc", "inspections.db")


def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS inspections (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number   TEXT,
            model           TEXT,
            technician      TEXT,
            date            TEXT,
            overall_status  TEXT,
            notes           TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS step_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_id   INTEGER REFERENCES inspections(id) ON DELETE CASCADE,
            step_num        INTEGER,
            step_name       TEXT,
            status          TEXT,
            details         TEXT,
            notes           TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_insp_serial ON inspections(serial_number);
        CREATE INDEX IF NOT EXISTS idx_insp_date   ON inspections(date);
    """)
    conn.commit()
    conn.close()


def save_inspection(state: dict) -> int:
    """Guarda el estado del wizard en la DB. Retorna el ID de la inspección."""
    from config import STATUS_PASSED, STATUS_FAILED, STATUS_SKIPPED, STATUS_PENDING
    STEP_NAMES = {
        1: "Bienvenida", 2: "Sistema", 3: "Teclado", 4: "Trackpad",
        5: "Pantalla", 6: "Cámara", 7: "Puertos USB", 8: "Red",
        9: "Audio", 10: "CPU", 11: "GPU", 12: "Memoria RAM",
        13: "Almacenamiento", 14: "Batería",
    }

    step_results = state.get("step_results", {})
    counts = {s: 0 for s in (STATUS_PASSED, STATUS_FAILED, STATUS_SKIPPED, STATUS_PENDING)}
    for n in range(1, 15):
        s = step_results.get(n, {}).get("status", STATUS_PENDING)
        if s in counts:
            counts[s] += 1

    if counts[STATUS_FAILED] == 0 and counts[STATUS_PASSED] + counts[STATUS_SKIPPED] == 14:
        overall = STATUS_PASSED
    elif counts[STATUS_FAILED] > 0:
        overall = STATUS_FAILED
    else:
        overall = STATUS_PENDING

    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO inspections (serial_number, model, technician, date, overall_status, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                state.get("device_serial", ""),
                state.get("device_model", ""),
                state.get("technician_name", ""),
                state.get("report_date", datetime.date.today().isoformat()),
                overall,
                state.get("final_notes", ""),
            )
        )
        inspection_id = cur.lastrowid

        for n in range(1, 15):
            result = step_results.get(n, {})
            conn.execute(
                """INSERT INTO step_results
                   (inspection_id, step_num, step_name, status, details, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    inspection_id,
                    n,
                    STEP_NAMES.get(n, f"Paso {n}"),
                    result.get("status", STATUS_PENDING),
                    result.get("details", ""),
                    result.get("notes", ""),
                )
            )
        conn.commit()
        return inspection_id
    finally:
        conn.close()


def get_recent_inspections(limit=100):
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT id, serial_number, model, technician, date,
                      overall_status, notes, created_at
               FROM inspections ORDER BY created_at DESC LIMIT ?""",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_inspection_steps(inspection_id: int):
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT step_num, step_name, status, details, notes
               FROM step_results WHERE inspection_id = ? ORDER BY step_num""",
            (inspection_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_inspections_by_serial(serial: str):
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT id, serial_number, model, technician, date,
                      overall_status, created_at
               FROM inspections WHERE serial_number = ?
               ORDER BY created_at DESC""",
            (serial,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_stats():
    conn = _get_conn()
    try:
        total   = conn.execute("SELECT COUNT(*) FROM inspections").fetchone()[0]
        passed  = conn.execute("SELECT COUNT(*) FROM inspections WHERE overall_status='passed'").fetchone()[0]
        failed  = conn.execute("SELECT COUNT(*) FROM inspections WHERE overall_status='failed'").fetchone()[0]
        today   = datetime.date.today().isoformat()
        today_c = conn.execute(
            "SELECT COUNT(*) FROM inspections WHERE date=?", (today,)
        ).fetchone()[0]
        return {"total": total, "passed": passed, "failed": failed, "today": today_c}
    finally:
        conn.close()
