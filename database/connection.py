import os
import sqlite3
from flask import current_app, has_app_context

from config import Config
from database.seed import seed_initial_data


def get_db_path() -> str:
    if has_app_context() and current_app.config.get('DATABASE_PATH'):
        return current_app.config['DATABASE_PATH']
    return Config.DATABASE_PATH


def get_db(db_path: str | None = None, isolation_level: str = '') -> sqlite3.Connection:
    resolved_path = db_path or get_db_path()
    parent_dir = os.path.dirname(resolved_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    conn = sqlite3.connect(resolved_path, timeout=30.0, isolation_level=isolation_level)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def _ensure_courses_columns(cursor: sqlite3.Cursor) -> None:
    existing_cols = {
        row['name']
        for row in cursor.execute("PRAGMA table_info(courses)").fetchall()
    }
    optional_cols = {
        'semester': "INTEGER DEFAULT 1",
        'class_name': "TEXT DEFAULT '1ATI'",
        'wp_type': "TEXT DEFAULT 'W'",
    }
    for col_name, col_def in optional_cols.items():
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE courses ADD COLUMN {col_name} {col_def}")


def init_db(db_path: str | None = None) -> None:
    conn = get_db(db_path=db_path)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            nim_nip TEXT NOT NULL,
            role TEXT NOT NULL,
            prodi TEXT NOT NULL,
            ipk REAL DEFAULT 0.0,
            semester INTEGER DEFAULT 1,
            dpa_id INTEGER,
            avatar TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            sks INTEGER NOT NULL,
            schedule_day TEXT NOT NULL,
            schedule_time TEXT NOT NULL,
            room TEXT NOT NULL,
            quota INTEGER NOT NULL DEFAULT 30,
            lecturer_id INTEGER,
            lecturer_name TEXT,
            status TEXT NOT NULL DEFAULT 'Menunggu',
            lecturer_agreed INTEGER DEFAULT 0,
            lecturer_dispensation_agreed INTEGER DEFAULT 0,
            semester INTEGER DEFAULT 1,
            class_name TEXT DEFAULT '1ATI',
            wp_type TEXT DEFAULT 'W',
            FOREIGN KEY (lecturer_id) REFERENCES users(id)
        )
        ''')
        _ensure_courses_columns(cursor)

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS krs_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            semester_period TEXT NOT NULL,
            total_sks INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Draft',
            dpa_notes TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified_at TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS krs_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Aktif',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES krs_applications(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id),
            UNIQUE(application_id, course_id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL UNIQUE,
            student_id INTEGER NOT NULL,
            va_number TEXT NOT NULL UNIQUE,
            bank_name TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Belum Lunas',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP,
            payment_channel TEXT,
            reconciliation_notes TEXT,
            FOREIGN KEY (application_id) REFERENCES krs_applications(id),
            FOREIGN KEY (student_id) REFERENCES users(id)
        )
        ''')

        seed_initial_data(conn)
        conn.commit()
    finally:
        conn.close()
