import sqlite3
import os
import random
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'academic.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
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
        role TEXT NOT NULL, -- 'mahasiswa', 'dpa', 'dosen', 'prodi', 'keuangan'
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
        status TEXT NOT NULL DEFAULT 'Menunggu', -- 'Menunggu', 'Dibuka', 'Dispensasi Buka', 'Dibatalkan'
        lecturer_agreed INTEGER DEFAULT 0, -- FR-10
        lecturer_dispensation_agreed INTEGER DEFAULT 0, -- FR-11
        semester INTEGER DEFAULT 1,
        class_name TEXT DEFAULT '1ATI',
        wp_type TEXT DEFAULT 'W',
        FOREIGN KEY (lecturer_id) REFERENCES users(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS krs_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        semester_period TEXT NOT NULL,
        total_sks INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Draft', 
        -- Status: 'Draft', 'Diajukan', 'Disetujui DPA', 'Ditolak DPA', 'Menunggu Pembayaran', 'Lunas'
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
        status TEXT NOT NULL DEFAULT 'Aktif', -- 'Aktif', 'Dibatalkan'
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
        status TEXT NOT NULL DEFAULT 'Belum Lunas', -- 'Belum Lunas', 'Lunas', 'Dibatalkan'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        paid_at TIMESTAMP,
        payment_channel TEXT,
        reconciliation_notes TEXT,
        FOREIGN KEY (application_id) REFERENCES krs_applications(id),
        FOREIGN KEY (student_id) REFERENCES users(id)
    )
    ''')

    # Default Configs
    default_configs = [
        ('registration_status', 'Buka'), # FR-14
        ('registration_start', '2026-07-01'),
        ('registration_end', '2026-07-25'),
        ('sks_rate', '220000'), # FR-21: SK Rektor 686/2025
        ('active_semester', 'Semester Antara 2026/2027'),
        ('max_sks', '9'), # SK Rektor 686/2025
        ('min_quota', '10') # Batas kuota standar kelas
    ]
    for k, v in default_configs:
        cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES (?, ?)", (k, v))

    # Seed Users
    seed_users = [
        ('1251420125', '123456', 'IHSAN MUBAROK', '1251420125', 'mahasiswa', 'Teknik Informatika', 3.75, 6, 5, '25110120414.png'),
        ('1251420128', '123456', 'DANUARDI SAPUTRO', '1251420128', 'mahasiswa', 'Teknik Informatika', 3.65, 6, 5, '25110120414.png'),
        ('1251420081', '123456', 'MUHAMMAD BAGAS F', '1251420081', 'mahasiswa', 'Teknik Informatika', 3.42, 6, 5, '25110120414.png'),
        ('1251420017', '123456', 'REVAND RADITIYA D', '1251420017', 'mahasiswa', 'Teknik Informatika', 3.58, 6, 5, '25110120414.png'),
        ('dpa1', '123456', 'Dr. Dewi Khairani, M.Sc.', '197805122005012001', 'dpa', 'Teknik Informatika', 0, 0, None, None),
        ('dosen1', '123456', 'Luh Kesuma Wardhani, S.T., M.T.', '198003152006042002', 'dosen', 'Teknik Informatika', 0, 0, None, None),
        ('prodi', '123456', 'Program Studi Teknik Informatika', 'ADMIN-PRODI-TIF', 'prodi', 'Teknik Informatika', 0, 0, None, None),
        ('keuangan', '123456', 'Biro Perencanaan dan Keuangan', 'BIRO-KEUANGAN-01', 'keuangan', 'Universitas', 0, 0, None, None)
    ]

    for u in seed_users:
        cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, name, nim_nip, role, prodi, ipk, semester, dpa_id, avatar)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', u)

    # Seed Courses (FR-03, FR-17, FR-18)
    seed_courses = [
        ('TIF3101', 'Rekayasa Perangkat Lunak', 3, 'Senin', '08.00 - 10.30 WIB', 'Lab RPL FST Lt. 3', 30, 6, 'Luh Kesuma Wardhani, S.T., M.T.', 'Dibuka', 1, 0),
        ('TIF3102', 'Basis Data Lanjut', 3, 'Selasa', '10.30 - 13.00 WIB', 'Ruang Teater FST Lt. 2', 25, 5, 'Dr. Dewi Khairani, M.Sc.', 'Dibuka', 1, 0),
        ('TIF3103', 'Pemrograman Berorientasi Objek', 3, 'Rabu', '08.00 - 10.30 WIB', 'Lab Komputer 2 Lt. 3', 30, 6, 'Luh Kesuma Wardhani, S.T., M.T.', 'Dibuka', 1, 0),
        ('TIF3104', 'Jaringan Komputer', 3, 'Kamis', '13.00 - 15.30 WIB', 'Lab Jaringan Lt. 3', 25, 6, 'Luh Kesuma Wardhani, S.T., M.T.', 'Menunggu', 0, 0),
        ('TIF3105', 'Sistem Informasi Enterprise', 3, 'Jumat', '08.00 - 10.30 WIB', 'Ruang Kelas 3.01 FST', 15, 5, 'Dr. Dewi Khairani, M.Sc.', 'Menunggu', 1, 0),
        ('TIF3106', 'Pengolahan Citra Digital', 3, 'Senin', '13.00 - 15.30 WIB', 'Ruang Kelas 3.02 FST', 20, 5, 'Dr. Dewi Khairani, M.Sc.', 'Menunggu', 0, 0)
    ]

    for c in seed_courses:
        cursor.execute('''
        INSERT OR IGNORE INTO courses (code, name, sks, schedule_day, schedule_time, room, quota, lecturer_id, lecturer_name, status, lecturer_agreed, lecturer_dispensation_agreed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', c)

    conn.commit()
    conn.close()

# Config helpers
def get_config(key, default=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM system_config WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row['value'] if row else default

def set_config(key, value):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

# User helpers
def get_user_by_id(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user

def get_user_by_username(username):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()
    return user

def get_users_by_role(role):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE role = ? ORDER BY name ASC", (role,))
    users = cur.fetchall()
    conn.close()
    return users

# FR-03 & FR-19: Courses list with participant counts and reliability check (NFR-03)
def get_courses_list():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    SELECT c.*, 
           COUNT(CASE WHEN ki.status = 'Aktif' THEN ki.id END) AS enrolled_count
    FROM courses c
    LEFT JOIN krs_items ki ON c.id = ki.course_id
    GROUP BY c.id
    ORDER BY c.semester ASC, c.code ASC
    ''')
    courses = cur.fetchall()
    conn.close()
    return courses

def get_courses_grouped_by_semester():
    courses = get_courses_list()
    grouped = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    for c in courses:
        sem = c['semester'] if c['semester'] in grouped else 1
        grouped[sem].append(c)
    return grouped

def get_course_by_id(course_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    SELECT c.*, 
           COUNT(CASE WHEN ki.status = 'Aktif' THEN ki.id END) AS enrolled_count
    FROM courses c
    LEFT JOIN krs_items ki ON c.id = ki.course_id
    WHERE c.id = ?
    GROUP BY c.id
    ''', (course_id,))
    course = cur.fetchone()
    conn.close()
    return course

# FR-17 & FR-18: Manage courses
def add_course(code, name, sks, day, time_str, room, quota, lecturer_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE id = ?", (lecturer_id,))
    lecturer = cur.fetchone()
    lecturer_name = lecturer['name'] if lecturer else ''
    
    cur.execute('''
    INSERT INTO courses (code, name, sks, schedule_day, schedule_time, room, quota, lecturer_id, lecturer_name, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Menunggu')
    ''', (code, name, sks, day, time_str, room, quota, lecturer_id, lecturer_name))
    conn.commit()
    conn.close()

def update_course_details(course_id, name, sks, day, time_str, room, quota, lecturer_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE id = ?", (lecturer_id,))
    lecturer = cur.fetchone()
    lecturer_name = lecturer['name'] if lecturer else ''

    cur.execute('''
    UPDATE courses 
    SET name = ?, sks = ?, schedule_day = ?, schedule_time = ?, room = ?, quota = ?, lecturer_id = ?, lecturer_name = ?
    WHERE id = ?
    ''', (name, sks, day, time_str, room, quota, lecturer_id, lecturer_name, course_id))
    conn.commit()
    conn.close()

def delete_course(course_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()

# FR-10 & FR-11: Lecturer confirmation
def confirm_lecturer_teaching(course_id, agreed):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE courses SET lecturer_agreed = ? WHERE id = ?", (1 if agreed else -1, course_id))
    # If agreed and status is still Menunggu, set to Dibuka if quota requirement is fine
    if agreed:
        cur.execute("UPDATE courses SET status = 'Dibuka' WHERE id = ? AND status = 'Menunggu'", (course_id,))
    conn.commit()
    conn.close()

def confirm_lecturer_dispensation(course_id, agreed):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE courses SET lecturer_dispensation_agreed = ? WHERE id = ?", (1 if agreed else -1, course_id))
    if agreed:
        cur.execute("UPDATE courses SET status = 'Dispensasi Buka' WHERE id = ?", (course_id,))
    else:
        cur.execute("UPDATE courses SET status = 'Dibatalkan' WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()

# FR-19: Class status management by Prodi
def update_course_status(course_id, new_status):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE courses SET status = ? WHERE id = ?", (new_status, course_id))
    
    # If course is cancelled ('Dibatalkan'), BR-07: mark krs_items as 'Dibatalkan'
    if new_status == 'Dibatalkan':
        cur.execute("UPDATE krs_items SET status = 'Dibatalkan' WHERE course_id = ?", (course_id,))
        # Recalculate total_sks for affected applications
        cur.execute('''
        SELECT DISTINCT application_id FROM krs_items WHERE course_id = ?
        ''', (course_id,))
        affected_apps = cur.fetchall()
        for app in affected_apps:
            recalculate_application_sks(app['application_id'])
    conn.commit()
    conn.close()

def recalculate_application_sks(app_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    SELECT COALESCE(SUM(c.sks), 0) as total
    FROM krs_items ki
    JOIN courses c ON ki.course_id = c.id
    WHERE ki.application_id = ? AND ki.status = 'Aktif'
    ''', (app_id,))
    row = cur.fetchone()
    total_sks = row['total'] if row else 0
    cur.execute("UPDATE krs_applications SET total_sks = ? WHERE id = ?", (total_sks, app_id))
    
    # Update invoice amount if invoice exists and not yet paid
    sks_rate = int(get_config('sks_rate', '220000'))
    cur.execute('''
    UPDATE invoices SET amount = ? WHERE application_id = ? AND status = 'Belum Lunas'
    ''', (total_sks * sks_rate, app_id))
    conn.commit()
    conn.close()

# FR-04 & NFR-03: Student KRS submission with atomic transaction and quota checking
def submit_student_krs(student_id, course_ids):
    """
    Submits KRS with validation:
    - Registration period must be open (FR-14)
    - Max 9 SKS (SK Rektor 686/2025)
    - Schedule conflict check
    - NFR-03: Concurrency & quota check to ensure class capacity is not exceeded
    """
    reg_status = get_config('registration_status', 'Buka')
    if reg_status != 'Buka':
        return False, "Periode pendaftaran Semester Antara sedang ditutup."

    if not course_ids:
        return False, "Pilih minimal 1 mata kuliah."

    conn = get_db()
    conn.isolation_level = 'EXCLUSIVE' # Guarantee strict serialization for NFR-03
    cur = conn.cursor()

    try:
        active_semester = get_config('active_semester', 'Semester Antara 2026/2027')
        max_sks = int(get_config('max_sks', '9'))

        # Fetch selected courses details
        placeholders = ','.join('?' for _ in course_ids)
        cur.execute(f"SELECT * FROM courses WHERE id IN ({placeholders})", course_ids)
        selected_courses = cur.fetchall()

        if len(selected_courses) != len(course_ids):
            conn.rollback()
            return False, "Beberapa mata kuliah yang dipilih tidak ditemukan."

        # 1. Total SKS Check
        total_sks = sum(c['sks'] for c in selected_courses)
        if total_sks > max_sks:
            conn.rollback()
            return False, f"Beban studi melebihi batas maksimal {max_sks} SKS (Anda memilih {total_sks} SKS) sesuai SK Rektor No. 686/2025."

        # 2. Schedule Conflict Check
        time_slots = {}
        for c in selected_courses:
            slot_key = f"{c['schedule_day']}_{c['schedule_time']}"
            if slot_key in time_slots:
                conn.rollback()
                conflict_course = time_slots[slot_key]
                return False, f"Terdapat bentrok jadwal antara mata kuliah '{c['name']}' dan '{conflict_course}' pada {c['schedule_day']}, {c['schedule_time']}."
            time_slots[slot_key] = c['name']

        # 3. NFR-03: Real-time Quota Availability Check
        for c in selected_courses:
            cur.execute('''
            SELECT COUNT(*) AS current_enrolled
            FROM krs_items ki
            JOIN krs_applications ka ON ki.application_id = ka.id
            WHERE ki.course_id = ? AND ki.status = 'Aktif' AND ka.student_id != ?
            ''', (c['id'], student_id))
            enrolled_row = cur.fetchone()
            current_enrolled = enrolled_row['current_enrolled'] if enrolled_row else 0
            
            if current_enrolled >= c['quota']:
                conn.rollback()
                return False, f"Kuota kelas untuk mata kuliah '{c['name']}' sudah penuh ({current_enrolled}/{c['quota']}). Pendaftaran dibatalkan."

        # 4. Check or Create Application
        cur.execute('''
        SELECT id, status FROM krs_applications 
        WHERE student_id = ? AND semester_period = ?
        ''', (student_id, active_semester))
        existing_app = cur.fetchone()

        if existing_app:
            app_id = existing_app['id']
            # Clear old items
            cur.execute("DELETE FROM krs_items WHERE application_id = ?", (app_id,))
            cur.execute('''
            UPDATE krs_applications 
            SET total_sks = ?, status = 'Diajukan', dpa_notes = NULL, submitted_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (total_sks, app_id))
        else:
            cur.execute('''
            INSERT INTO krs_applications (student_id, semester_period, total_sks, status)
            VALUES (?, ?, ?, 'Diajukan')
            ''', (student_id, active_semester, total_sks))
            app_id = cur.lastrowid

        # Insert new items
        for cid in course_ids:
            cur.execute('''
            INSERT INTO krs_items (application_id, course_id, status)
            VALUES (?, ?, 'Aktif')
            ''', (app_id, cid))

        conn.commit()
        return True, "Kartu Rencana Studi (KRS) berhasil diajukan dan sedang menunggu verifikasi Dosen Pembimbing Akademik."

    except Exception as e:
        conn.rollback()
        return False, f"Terjadi kesalahan saat menyimpan KRS: {str(e)}"
    finally:
        conn.close()

# Get student application and items
def get_student_application(student_id):
    active_semester = get_config('active_semester', 'Semester Antara 2026/2027')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    SELECT ka.*, u.name as student_name, u.nim_nip, u.prodi, u.ipk, dpa.name as dpa_name
    FROM krs_applications ka
    JOIN users u ON ka.student_id = u.id
    LEFT JOIN users dpa ON u.dpa_id = dpa.id
    WHERE ka.student_id = ? AND ka.semester_period = ?
    ''', (student_id, active_semester))
    app = cur.fetchone()

    items = []
    invoice = None
    if app:
        cur.execute('''
        SELECT ki.*, c.code, c.name, c.sks, c.schedule_day, c.schedule_time, c.room, c.lecturer_name, c.status as course_status
        FROM krs_items ki
        JOIN courses c ON ki.course_id = c.id
        WHERE ki.application_id = ?
        ''', (app['id'],))
        items = cur.fetchall()

        cur.execute("SELECT * FROM invoices WHERE application_id = ?", (app['id'],))
        invoice = cur.fetchone()

    conn.close()
    return app, items, invoice

# FR-08 & FR-09: DPA functions
def get_dpa_applications(dpa_id):
    active_semester = get_config('active_semester', 'Semester Antara 2026/2027')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    SELECT ka.*, u.name as student_name, u.nim_nip, u.prodi, u.ipk, u.semester
    FROM krs_applications ka
    JOIN users u ON ka.student_id = u.id
    WHERE u.dpa_id = ? AND ka.semester_period = ?
    ORDER BY ka.submitted_at DESC
    ''', (dpa_id, active_semester))
    apps = cur.fetchall()
    conn.close()
    return apps

def approve_student_krs(application_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    UPDATE krs_applications 
    SET status = 'Disetujui DPA', verified_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (application_id,))

    # FR-22: Automatic Virtual Account generation upon approval
    cur.execute("SELECT * FROM krs_applications WHERE id = ?", (application_id,))
    app = cur.fetchone()

    if app:
        cur.execute("SELECT * FROM invoices WHERE application_id = ?", (application_id,))
        existing_inv = cur.fetchone()
        if not existing_inv:
            cur.execute("SELECT nim_nip FROM users WHERE id = ?", (app['student_id'],))
            student = cur.fetchone()
            nim = student['nim_nip'] if student else '00000000'
            sks_rate = int(get_config('sks_rate', '220000'))
            amount = app['total_sks'] * sks_rate
            
            # Generate 16 digit VA: Bank Mandiri prefix 8871 + NIM (padded/truncated) + random suffix
            va_number = f"8871{nim[-6:]}{random.randint(1000, 9999)}"
            banks = ['Bank Mandiri', 'Bank Syariah Indonesia (BSI)', 'BNI', 'BRI']
            chosen_bank = banks[0]

            cur.execute('''
            INSERT INTO invoices (application_id, student_id, va_number, bank_name, amount, status)
            VALUES (?, ?, ?, ?, ?, 'Belum Lunas')
            ''', (application_id, app['student_id'], va_number, chosen_bank, amount))

    conn.commit()
    conn.close()

def reject_student_krs(application_id, notes):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    UPDATE krs_applications 
    SET status = 'Ditolak DPA', dpa_notes = ?, verified_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (notes, application_id))
    conn.commit()
    conn.close()

# FR-21, FR-22, FR-23: Keuangan functions
def get_all_invoices():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    SELECT inv.*, u.name as student_name, u.nim_nip, u.prodi, ka.total_sks, ka.semester_period
    FROM invoices inv
    JOIN users u ON inv.student_id = u.id
    JOIN krs_applications ka ON inv.application_id = ka.id
    ORDER BY inv.created_at DESC
    ''')
    invoices = cur.fetchall()
    conn.close()
    return invoices

def reconcile_manual_payment(invoice_id, ref_no, notes):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    UPDATE invoices 
    SET status = 'Lunas', paid_at = CURRENT_TIMESTAMP, payment_channel = 'Rekonsiliasi Manual Bank',
        reconciliation_notes = ?
    WHERE id = ?
    ''', (f"Ref: {ref_no} | {notes}", invoice_id))

    # Update KRS application status to Lunas
    cur.execute("SELECT application_id FROM invoices WHERE id = ?", (invoice_id,))
    inv = cur.fetchone()
    if inv:
        cur.execute("UPDATE krs_applications SET status = 'Lunas' WHERE id = ?", (inv['application_id'],))

    conn.commit()
    conn.close()

# FR-20: Official participant export data
def get_official_participants():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    SELECT u.nim_nip, u.name as student_name, u.prodi,
           c.code as course_code, c.name as course_name, c.sks, c.room, c.schedule_day, c.schedule_time,
           c.lecturer_name, c.status as class_status,
           ka.status as krs_status,
           COALESCE(inv.status, 'Belum Terbit Tagihan') as payment_status,
           inv.va_number
    FROM krs_items ki
    JOIN courses c ON ki.course_id = c.id
    JOIN krs_applications ka ON ki.application_id = ka.id
    JOIN users u ON ka.student_id = u.id
    LEFT JOIN invoices inv ON ka.id = inv.application_id
    WHERE ki.status = 'Aktif'
    ORDER BY c.code ASC, u.nim_nip ASC
    ''')
    participants = cur.fetchall()
    conn.close()
    return participants
