import os
import sqlite3
from flask import current_app, has_app_context

from config import Config, normalize_database_url
from database.seed import seed_initial_data

try:
    import psycopg
    from psycopg.rows import dict_row
    DB_INTEGRITY_ERRORS: tuple[type[BaseException], ...] = (
        sqlite3.IntegrityError,
        psycopg.IntegrityError,
    )
except ImportError:
    psycopg = None
    dict_row = None
    DB_INTEGRITY_ERRORS = (sqlite3.IntegrityError,)

_UNSET = object()


def translate_placeholders(sql: str) -> str:
    """Translate SQLite '?' placeholders outside single-quoted literals to '%s' for PostgreSQL."""
    out: list[str] = []
    in_quote = False
    i = 0
    length = len(sql)
    while i < length:
        ch = sql[i]
        if ch == "'":
            out.append(ch)
            if in_quote and i + 1 < length and sql[i + 1] == "'":
                out.append("'")
                i += 2
                continue
            in_quote = not in_quote
        elif ch == '?' and not in_quote:
            out.append('%s')
        else:
            out.append(ch)
        i += 1
    return ''.join(out)


class CompatConnection:
    """Thin database connection adapter providing consistent behavior on SQLite and PostgreSQL."""

    def __init__(self, raw_conn, backend: str):
        self._conn = raw_conn
        self.backend = backend

    @property
    def is_postgres(self) -> bool:
        return self.backend == 'postgres'

    def cursor(self):
        return self

    def execute(self, sql: str, params=()):
        if self.is_postgres:
            pg_sql = translate_placeholders(sql)
            return self._conn.execute(pg_sql, params or ())
        return self._conn.execute(sql, params or ())

    def executemany(self, sql: str, seq_of_params):
        if self.is_postgres:
            pg_sql = translate_placeholders(sql)
            with self._conn.cursor() as cur:
                cur.executemany(pg_sql, seq_of_params)
            return cur
        return self._conn.executemany(sql, seq_of_params)

    def insert_returning_id(self, sql: str, params=(), id_col: str = 'id') -> int:
        if self.is_postgres:
            stripped = sql.rstrip().rstrip(';')
            if 'returning ' not in stripped.lower():
                stripped = f"{stripped} RETURNING {id_col}"
            row = self.execute(stripped, params).fetchone()
            return int(row[id_col])
        cur = self.execute(sql, params)
        return int(cur.lastrowid)

    def begin_exclusive(self) -> None:
        if self.is_postgres:
            self.execute("BEGIN")
        else:
            self.execute("BEGIN EXCLUSIVE")

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        self._conn.close()


def get_db_url() -> str | None:
    if has_app_context() and 'DATABASE_URL' in current_app.config:
        return normalize_database_url(current_app.config.get('DATABASE_URL'))
    return Config.DATABASE_URL


def get_db_path() -> str:
    if has_app_context() and current_app.config.get('DATABASE_PATH'):
        return current_app.config['DATABASE_PATH']
    return Config.DATABASE_PATH


def get_db(
    db_path: str | None = None,
    database_url: object = _UNSET,
    isolation_level: str | None = '',
) -> CompatConnection:
    resolved_url = (
        get_db_url()
        if database_url is _UNSET
        else normalize_database_url(database_url)
    )

    if resolved_url:
        if psycopg is None or dict_row is None:
            raise RuntimeError(
                "Driver PostgreSQL 'psycopg[binary]' belum terpasang. "
                "Jalankan: pip install -r requirements.txt"
            )
        autocommit = isolation_level is None
        raw_pg = psycopg.connect(
            resolved_url,
            row_factory=dict_row,
            connect_timeout=10,
            prepare_threshold=None,
            autocommit=autocommit,
        )
        return CompatConnection(raw_pg, backend='postgres')

    resolved_path = db_path or get_db_path()
    parent_dir = os.path.dirname(resolved_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    raw_sqlite = sqlite3.connect(
        resolved_path,
        timeout=30.0,
        isolation_level=isolation_level,
    )
    raw_sqlite.row_factory = sqlite3.Row
    raw_sqlite.execute("PRAGMA foreign_keys = ON")
    raw_sqlite.execute("PRAGMA busy_timeout = 30000")
    return CompatConnection(raw_sqlite, backend='sqlite')


def _ensure_sqlite_table_columns(conn: CompatConnection, table: str, cols: dict[str, str]) -> None:
    existing_cols = {
        row['name']
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    for col_name, col_def in cols.items():
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")


def _init_postgres_schema(conn: CompatConnection) -> None:
    def _is_ready() -> bool:
        tbl_row = conn.execute("SELECT to_regclass('public.invoices') AS tbl").fetchone()
        if not (tbl_row and tbl_row['tbl']):
            return False

        col_email = conn.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'email'
            """
        ).fetchone()
        col_lec = conn.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'krs_applications' AND column_name = 'lecturer_approval'
            """
        ).fetchone()
        if not (col_email and col_lec):
            return False

        cfg_cnt = conn.execute("SELECT COUNT(*) AS cnt FROM system_config").fetchone()['cnt']
        has_superadmin = conn.execute(
            "SELECT 1 FROM users WHERE username = 'superadmin'"
        ).fetchone()
        return bool(cfg_cnt >= 7 and has_superadmin)

    if _is_ready():
        conn.commit()
        return

    conn.execute("SELECT pg_advisory_xact_lock(6862025)")
    if _is_ready():
        conn.commit()
        return

    conn.execute('''
    CREATE TABLE IF NOT EXISTS system_config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        nim_nip TEXT NOT NULL,
        role TEXT NOT NULL,
        prodi TEXT NOT NULL,
        ipk DOUBLE PRECISION DEFAULT 0.0,
        semester INTEGER DEFAULT 1,
        dpa_id INTEGER,
        avatar TEXT,
        email TEXT,
        is_active INTEGER DEFAULT 1
    )
    ''')
    conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT")
    conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active INTEGER DEFAULT 1")

    conn.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id SERIAL PRIMARY KEY,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        sks INTEGER NOT NULL,
        schedule_day TEXT NOT NULL,
        schedule_time TEXT NOT NULL,
        room TEXT NOT NULL,
        quota INTEGER NOT NULL DEFAULT 30,
        lecturer_id INTEGER REFERENCES users(id),
        lecturer_name TEXT,
        status TEXT NOT NULL DEFAULT 'Menunggu',
        lecturer_agreed INTEGER DEFAULT 0,
        lecturer_dispensation_agreed INTEGER DEFAULT 0,
        semester INTEGER DEFAULT 1,
        class_name TEXT DEFAULT '1ATI',
        wp_type TEXT DEFAULT 'W'
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS krs_applications (
        id SERIAL PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES users(id),
        semester_period TEXT NOT NULL,
        total_sks INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Draft',
        dpa_notes TEXT,
        lecturer_approval TEXT DEFAULT 'Menunggu',
        lecturer_notes TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified_at TIMESTAMP
    )
    ''')
    conn.execute(
        "ALTER TABLE krs_applications ADD COLUMN IF NOT EXISTS lecturer_approval TEXT DEFAULT 'Menunggu'"
    )
    conn.execute("ALTER TABLE krs_applications ADD COLUMN IF NOT EXISTS lecturer_notes TEXT")

    conn.execute('''
    CREATE TABLE IF NOT EXISTS krs_items (
        id SERIAL PRIMARY KEY,
        application_id INTEGER NOT NULL REFERENCES krs_applications(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id),
        status TEXT NOT NULL DEFAULT 'Aktif',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(application_id, course_id)
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id SERIAL PRIMARY KEY,
        application_id INTEGER NOT NULL UNIQUE REFERENCES krs_applications(id),
        student_id INTEGER NOT NULL REFERENCES users(id),
        va_number TEXT NOT NULL UNIQUE,
        bank_name TEXT NOT NULL,
        amount INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Belum Lunas',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        paid_at TIMESTAMP,
        payment_channel TEXT,
        reconciliation_notes TEXT
    )
    ''')

    seed_initial_data(conn)
    conn.commit()


def _init_sqlite_schema(conn: CompatConnection) -> None:
    conn.execute("PRAGMA journal_mode = WAL")

    conn.execute('''
    CREATE TABLE IF NOT EXISTS system_config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')

    conn.execute('''
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
        avatar TEXT,
        email TEXT,
        is_active INTEGER DEFAULT 1
    )
    ''')
    _ensure_sqlite_table_columns(
        conn,
        'users',
        {
            'email': 'TEXT',
            'is_active': 'INTEGER DEFAULT 1',
        },
    )

    conn.execute('''
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
    _ensure_sqlite_table_columns(
        conn,
        'courses',
        {
            'semester': 'INTEGER DEFAULT 1',
            'class_name': "TEXT DEFAULT '1ATI'",
            'wp_type': "TEXT DEFAULT 'W'",
        },
    )

    conn.execute('''
    CREATE TABLE IF NOT EXISTS krs_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        semester_period TEXT NOT NULL,
        total_sks INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Draft',
        dpa_notes TEXT,
        lecturer_approval TEXT DEFAULT 'Menunggu',
        lecturer_notes TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified_at TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users(id)
    )
    ''')
    _ensure_sqlite_table_columns(
        conn,
        'krs_applications',
        {
            'lecturer_approval': "TEXT DEFAULT 'Menunggu'",
            'lecturer_notes': 'TEXT',
        },
    )

    conn.execute('''
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

    conn.execute('''
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


def init_db(db_path: str | None = None, database_url: object = _UNSET) -> None:
    conn = get_db(db_path=db_path, database_url=database_url)
    try:
        if conn.is_postgres:
            _init_postgres_schema(conn)
        else:
            _init_sqlite_schema(conn)
    finally:
        conn.close()
