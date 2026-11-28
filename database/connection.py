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
        tbl_cnt = conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN (
                  'invoices', 'programs', 'announcements',
                  'student_grades', 'course_equivalences', 'course_proposals'
              )
            """
        ).fetchone()['cnt']
        if tbl_cnt < 6:
            return False

        col_cnt = conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM information_schema.columns
            WHERE table_schema = 'public'
              AND (
                  (table_name = 'users' AND column_name = 'status_sanksi')
                  OR (table_name = 'courses' AND column_name = 'dispensation_requested')
                  OR (table_name = 'krs_applications' AND column_name = 'preferred_bank')
                  OR (table_name = 'krs_items' AND column_name = 'jenis_pengambilan')
                  OR (table_name = 'invoices' AND column_name = 'expires_at')
              )
            """
        ).fetchone()['cnt']
        if col_cnt < 5:
            return False

        cfg_cnt = conn.execute("SELECT COUNT(*) AS cnt FROM system_config").fetchone()['cnt']
        has_dpa = conn.execute("SELECT 1 FROM users WHERE username = 'dpa1' AND role = 'dpa'").fetchone()
        has_prodi = conn.execute("SELECT 1 FROM users WHERE username = 'prodi' AND role = 'prodi'").fetchone()
        has_keu = conn.execute("SELECT 1 FROM users WHERE username = 'keuangan' AND role = 'keuangan'").fetchone()
        has_super = conn.execute("SELECT 1 FROM users WHERE username = 'superadmin'").fetchone()
        return bool(cfg_cnt >= 10 and has_dpa and has_prodi and has_keu and has_super)

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
    CREATE TABLE IF NOT EXISTS programs (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        faculty TEXT NOT NULL,
        rumpun_ilmu TEXT NOT NULL DEFAULT 'Sarjana Reguler',
        status_buka_sa TEXT NOT NULL DEFAULT 'Menyelenggarakan'
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
        prodi_code TEXT DEFAULT '60',
        ipk DOUBLE PRECISION DEFAULT 0.0,
        semester INTEGER DEFAULT 1,
        status_sanksi TEXT DEFAULT 'Aktif Bebas Sanksi',
        dpa_id INTEGER,
        avatar TEXT,
        email TEXT,
        jabatan_fungsional TEXT,
        no_hp TEXT,
        is_active INTEGER DEFAULT 1
    )
    ''')
    conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT")
    conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active INTEGER DEFAULT 1")
    conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS prodi_code TEXT DEFAULT '60'")
    conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS status_sanksi TEXT DEFAULT 'Aktif Bebas Sanksi'")
    conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS jabatan_fungsional TEXT")
    conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS no_hp TEXT")

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
        min_quota INTEGER NOT NULL DEFAULT 10,
        lecturer_id INTEGER REFERENCES users(id),
        lecturer_name TEXT,
        prodi_code TEXT NOT NULL DEFAULT '60',
        prodi_name TEXT NOT NULL DEFAULT 'Teknik Informatika',
        status TEXT NOT NULL DEFAULT 'Menunggu',
        lecturer_agreed INTEGER DEFAULT 0,
        lecturer_dispensation_agreed INTEGER DEFAULT 0,
        dispensation_requested INTEGER DEFAULT 0,
        allow_cross_prodi INTEGER DEFAULT 1,
        semester INTEGER DEFAULT 1,
        class_name TEXT DEFAULT '1ATI',
        wp_type TEXT DEFAULT 'W'
    )
    ''')
    conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS min_quota INTEGER DEFAULT 10")
    conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS prodi_code TEXT DEFAULT '60'")
    conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS prodi_name TEXT DEFAULT 'Teknik Informatika'")
    conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS dispensation_requested INTEGER DEFAULT 0")
    conn.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS allow_cross_prodi INTEGER DEFAULT 1")

    conn.execute('''
    CREATE TABLE IF NOT EXISTS student_grades (
        id SERIAL PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_code TEXT NOT NULL,
        grade TEXT NOT NULL,
        semester_taken INTEGER DEFAULT 1,
        UNIQUE(student_id, course_code)
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS announcements (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'Jadwal & Ketentuan',
        is_active INTEGER NOT NULL DEFAULT 1,
        created_by INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS course_equivalences (
        id SERIAL PRIMARY KEY,
        equivalence_code TEXT UNIQUE NOT NULL,
        kode_mk_asal TEXT NOT NULL,
        nama_mk_asal TEXT NOT NULL,
        prodi_asal_code TEXT NOT NULL,
        kode_mk_tujuan TEXT NOT NULL,
        nama_mk_tujuan TEXT NOT NULL,
        prodi_tujuan_code TEXT NOT NULL,
        sks INTEGER NOT NULL DEFAULT 3,
        status_ekuivalen TEXT NOT NULL DEFAULT 'Valid',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS course_proposals (
        id SERIAL PRIMARY KEY,
        proposal_code TEXT UNIQUE NOT NULL,
        student_id INTEGER NOT NULL REFERENCES users(id),
        target_prodi_code TEXT NOT NULL DEFAULT '60',
        course_code TEXT NOT NULL,
        course_name TEXT NOT NULL,
        sks INTEGER NOT NULL DEFAULT 3,
        semester_target INTEGER NOT NULL DEFAULT 1,
        is_cross_prodi INTEGER NOT NULL DEFAULT 0,
        origin_course_code TEXT,
        origin_course_name TEXT,
        syllabus_summary TEXT,
        reason TEXT,
        status TEXT NOT NULL DEFAULT 'Menunggu Persetujuan',
        prodi_asal_status TEXT NOT NULL DEFAULT 'Menunggu',
        prodi_tujuan_status TEXT NOT NULL DEFAULT 'Menunggu',
        equivalence_note TEXT,
        admin_notes TEXT,
        lecturer_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reviewed_at TIMESTAMP
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS krs_applications (
        id SERIAL PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES users(id),
        semester_period TEXT NOT NULL,
        total_sks INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Draft',
        status_final TEXT NOT NULL DEFAULT 'Draft',
        dpa_notes TEXT,
        dpa_verified_by INTEGER,
        preferred_bank TEXT DEFAULT 'Bank Mandiri',
        lecturer_approval TEXT DEFAULT 'Menunggu',
        lecturer_notes TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified_at TIMESTAMP
    )
    ''')
    conn.execute("ALTER TABLE krs_applications ADD COLUMN IF NOT EXISTS status_final TEXT DEFAULT 'Draft'")
    conn.execute("ALTER TABLE krs_applications ADD COLUMN IF NOT EXISTS dpa_verified_by INTEGER")
    conn.execute("ALTER TABLE krs_applications ADD COLUMN IF NOT EXISTS preferred_bank TEXT DEFAULT 'Bank Mandiri'")
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
        jenis_pengambilan TEXT NOT NULL DEFAULT 'Perbaikan Nilai',
        nilai_lama TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(application_id, course_id)
    )
    ''')
    conn.execute(
        "ALTER TABLE krs_items ADD COLUMN IF NOT EXISTS jenis_pengambilan TEXT DEFAULT 'Perbaikan Nilai'"
    )
    conn.execute("ALTER TABLE krs_items ADD COLUMN IF NOT EXISTS nilai_lama TEXT")

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
        expires_at TIMESTAMP,
        paid_at TIMESTAMP,
        payment_channel TEXT,
        reconciliation_notes TEXT
    )
    ''')
    conn.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP")

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
    CREATE TABLE IF NOT EXISTS programs (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        faculty TEXT NOT NULL,
        rumpun_ilmu TEXT NOT NULL DEFAULT 'Sarjana Reguler',
        status_buka_sa TEXT NOT NULL DEFAULT 'Menyelenggarakan'
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
        prodi_code TEXT DEFAULT '60',
        ipk REAL DEFAULT 0.0,
        semester INTEGER DEFAULT 1,
        status_sanksi TEXT DEFAULT 'Aktif Bebas Sanksi',
        dpa_id INTEGER,
        avatar TEXT,
        email TEXT,
        jabatan_fungsional TEXT,
        no_hp TEXT,
        is_active INTEGER DEFAULT 1
    )
    ''')
    _ensure_sqlite_table_columns(
        conn,
        'users',
        {
            'email': 'TEXT',
            'is_active': 'INTEGER DEFAULT 1',
            'prodi_code': "TEXT DEFAULT '60'",
            'status_sanksi': "TEXT DEFAULT 'Aktif Bebas Sanksi'",
            'jabatan_fungsional': 'TEXT',
            'no_hp': 'TEXT',
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
        min_quota INTEGER NOT NULL DEFAULT 10,
        lecturer_id INTEGER,
        lecturer_name TEXT,
        prodi_code TEXT NOT NULL DEFAULT '60',
        prodi_name TEXT NOT NULL DEFAULT 'Teknik Informatika',
        status TEXT NOT NULL DEFAULT 'Menunggu',
        lecturer_agreed INTEGER DEFAULT 0,
        lecturer_dispensation_agreed INTEGER DEFAULT 0,
        dispensation_requested INTEGER DEFAULT 0,
        allow_cross_prodi INTEGER DEFAULT 1,
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
            'min_quota': 'INTEGER DEFAULT 10',
            'prodi_code': "TEXT DEFAULT '60'",
            'prodi_name': "TEXT DEFAULT 'Teknik Informatika'",
            'dispensation_requested': 'INTEGER DEFAULT 0',
            'allow_cross_prodi': 'INTEGER DEFAULT 1',
        },
    )

    conn.execute('''
    CREATE TABLE IF NOT EXISTS student_grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_code TEXT NOT NULL,
        grade TEXT NOT NULL,
        semester_taken INTEGER DEFAULT 1,
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(student_id, course_code)
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'Jadwal & Ketentuan',
        is_active INTEGER NOT NULL DEFAULT 1,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS course_equivalences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equivalence_code TEXT UNIQUE NOT NULL,
        kode_mk_asal TEXT NOT NULL,
        nama_mk_asal TEXT NOT NULL,
        prodi_asal_code TEXT NOT NULL,
        kode_mk_tujuan TEXT NOT NULL,
        nama_mk_tujuan TEXT NOT NULL,
        prodi_tujuan_code TEXT NOT NULL,
        sks INTEGER NOT NULL DEFAULT 3,
        status_ekuivalen TEXT NOT NULL DEFAULT 'Valid',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS course_proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proposal_code TEXT UNIQUE NOT NULL,
        student_id INTEGER NOT NULL,
        target_prodi_code TEXT NOT NULL DEFAULT '60',
        course_code TEXT NOT NULL,
        course_name TEXT NOT NULL,
        sks INTEGER NOT NULL DEFAULT 3,
        semester_target INTEGER NOT NULL DEFAULT 1,
        is_cross_prodi INTEGER NOT NULL DEFAULT 0,
        origin_course_code TEXT,
        origin_course_name TEXT,
        syllabus_summary TEXT,
        reason TEXT,
        status TEXT NOT NULL DEFAULT 'Menunggu Persetujuan',
        prodi_asal_status TEXT NOT NULL DEFAULT 'Menunggu',
        prodi_tujuan_status TEXT NOT NULL DEFAULT 'Menunggu',
        equivalence_note TEXT,
        admin_notes TEXT,
        lecturer_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reviewed_at TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users(id),
        FOREIGN KEY (lecturer_id) REFERENCES users(id)
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS krs_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        semester_period TEXT NOT NULL,
        total_sks INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Draft',
        status_final TEXT NOT NULL DEFAULT 'Draft',
        dpa_notes TEXT,
        dpa_verified_by INTEGER,
        preferred_bank TEXT DEFAULT 'Bank Mandiri',
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
            'status_final': "TEXT DEFAULT 'Draft'",
            'dpa_verified_by': 'INTEGER',
            'preferred_bank': "TEXT DEFAULT 'Bank Mandiri'",
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
        jenis_pengambilan TEXT NOT NULL DEFAULT 'Perbaikan Nilai',
        nilai_lama TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES krs_applications(id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(id),
        UNIQUE(application_id, course_id)
    )
    ''')
    _ensure_sqlite_table_columns(
        conn,
        'krs_items',
        {
            'jenis_pengambilan': "TEXT DEFAULT 'Perbaikan Nilai'",
            'nilai_lama': 'TEXT',
        },
    )

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
        expires_at TIMESTAMP,
        paid_at TIMESTAMP,
        payment_channel TEXT,
        reconciliation_notes TEXT,
        FOREIGN KEY (application_id) REFERENCES krs_applications(id),
        FOREIGN KEY (student_id) REFERENCES users(id)
    )
    ''')
    _ensure_sqlite_table_columns(
        conn,
        'invoices',
        {
            'expires_at': 'TIMESTAMP',
        },
    )

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
