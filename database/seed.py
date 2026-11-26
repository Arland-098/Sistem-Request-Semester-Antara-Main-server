import sqlite3

DEFAULT_CONFIGS = [
    ('registration_status', 'Buka'),
    ('registration_start', '2026-07-01'),
    ('registration_end', '2026-07-25'),
    ('sks_rate', '220000'),
    ('active_semester', 'Semester Antara 2026/2027'),
    ('max_sks', '9'),
    ('min_quota', '10'),
]

SEED_USERS = [
    ('1251420125', '123456', 'IHSAN MUBAROK', '1251420125', 'mahasiswa', 'Teknik Informatika', 3.75, 6, 5, '25110120414.png'),
    ('1251420128', '123456', 'DANUARDI SAPUTRO', '1251420128', 'mahasiswa', 'Teknik Informatika', 3.65, 6, 5, '25110120414.png'),
    ('1251420081', '123456', 'MUHAMMAD BAGAS F', '1251420081', 'mahasiswa', 'Teknik Informatika', 3.42, 6, 5, '25110120414.png'),
    ('1251420017', '123456', 'REVAND RADITIYA D', '1251420017', 'mahasiswa', 'Teknik Informatika', 3.58, 6, 5, '25110120414.png'),
    ('dpa1', '123456', 'Dr. Dewi Khairani, M.Sc.', '197805122005012001', 'dpa', 'Teknik Informatika', 0.0, 0, None, None),
    ('dosen1', '123456', 'Luh Kesuma Wardhani, S.T., M.T.', '198003152006042002', 'dosen', 'Teknik Informatika', 0.0, 0, None, None),
    ('prodi', '123456', 'Program Studi Teknik Informatika', 'ADMIN-PRODI-TIF', 'prodi', 'Teknik Informatika', 0.0, 0, None, None),
    ('keuangan', '123456', 'Biro Perencanaan dan Keuangan', 'BIRO-KEUANGAN-01', 'keuangan', 'Universitas', 0.0, 0, None, None),
]

# Full 45-course catalog for Paket Semester 1 s.d. 6 (Program Studi Teknik Informatika UIN Jakarta)
SEED_COURSES = [
    # Semester 1
    ('FST6091101', 'Dasar-dasar Pemrograman', 3, 'Senin', '08.00 - 10.30 WIB', 'Lab Komputer 1 Lt. 3', 33, 6, 'Luh Kesuma Wardhani, S.T., M.T.', 'Dibuka', 1, 0, 1, '1ATI', 'W'),
    ('FST6091125', 'Elektronika Dasar', 3, 'Selasa', '08.00 - 10.30 WIB', 'Lab Hardware Lt. 2', 33, None, 'Feri Fahrianto, M.Sc.,Ph.D', 'Dibuka', 1, 0, 1, '1BTI', 'W'),
    ('FST6091201', 'Literasi Digital', 2, 'Rabu', '08.00 - 09.40 WIB', 'Ruang Teater FST Lt. 2', 33, None, 'Victor Amrizal, M.Kom.', 'Dibuka', 1, 0, 1, '1CTI', 'W'),
    ('FST6094102', 'Matematika Diskrit', 4, 'Kamis', '08.00 - 11.20 WIB', 'Ruang Kelas 3.01 FST', 33, None, 'Luh Kesuma Wardhani, S.T., M.T.', 'Dibuka', 1, 0, 1, '1DTI', 'W'),
    ('NAS6112203', 'Pendidikan Kewarganegaraan', 2, 'Jumat', '08.00 - 09.40 WIB', 'Ruang Kelas 3.02 FST', 33, None, 'Nurul Faizah Rozy, MTI', 'Dibuka', 1, 0, 1, '1ETI', 'W'),
    ('UIN6032205', 'Praktikum Qira’ah dan Ibadah', 2, 'Senin', '13.00 - 14.40 WIB', 'Masjid FST Lt. 1', 33, None, 'Drs.M. Tabah Rosyadi, M.A.', 'Dibuka', 1, 0, 1, '1ATI', 'W'),
    ('UIN6033201', 'Studi Islam', 4, 'Selasa', '13.00 - 16.20 WIB', 'Ruang Teater FST Lt. 2', 33, None, 'Burhanuddin, M.A.', 'Dibuka', 1, 0, 1, '1BTI', 'W'),
    ('TIF3101', 'Rekayasa Perangkat Lunak', 3, 'Senin', '08.00 - 10.30 WIB', 'Lab RPL FST Lt. 3', 30, 6, 'Luh Kesuma Wardhani, S.T., M.T.', 'Dibuka', 1, 0, 1, '1ATI', 'W'),
    ('TIF3102', 'Basis Data Lanjut', 3, 'Selasa', '10.30 - 13.00 WIB', 'Ruang Teater FST Lt. 2', 25, 5, 'Dr. Dewi Khairani, M.Sc.', 'Dibuka', 1, 0, 1, '1ATI', 'W'),
    ('TIF3103', 'Pemrograman Berorientasi Objek', 3, 'Rabu', '08.00 - 10.30 WIB', 'Lab Komputer 2 Lt. 3', 30, 6, 'Luh Kesuma Wardhani, S.T., M.T.', 'Dibuka', 1, 0, 1, '1ATI', 'W'),
    ('TIF3104', 'Jaringan Komputer', 3, 'Kamis', '13.00 - 15.30 WIB', 'Lab Jaringan Lt. 3', 25, 6, 'Luh Kesuma Wardhani, S.T., M.T.', 'Menunggu', 0, 0, 1, '1ATI', 'W'),
    ('TIF3105', 'Sistem Informasi Enterprise', 3, 'Jumat', '08.00 - 10.30 WIB', 'Ruang Kelas 3.01 FST', 15, 5, 'Dr. Dewi Khairani, M.Sc.', 'Menunggu', 1, 0, 1, '1ATI', 'W'),
    ('TIF3106', 'Pengolahan Citra Digital', 3, 'Senin', '13.00 - 15.30 WIB', 'Ruang Kelas 3.02 FST', 20, 5, 'Dr. Dewi Khairani, M.Sc.', 'Menunggu', 0, 0, 1, '1ATI', 'W'),

    # Semester 2
    ('UIN6033205', 'Praktikum Qira’ah dan Ibadah', 2, 'Rabu', '13.00 - 14.40 WIB', 'Masjid FST Lt. 1', 10, None, 'Drs.M. Tabah Rosyadi, M.A.', 'Dibuka', 1, 0, 2, '120TI', 'W'),
    ('FST6091102', 'Algoritma dan Pemrograman Lanjut', 3, 'Kamis', '13.00 - 15.30 WIB', 'Lab Komputer 2 Lt. 3', 35, None, 'Nurhayati, Ph.D.', 'Dibuka', 1, 0, 2, '2ATI', 'W'),
    ('FST6091104', 'Matematika Informatika I', 3, 'Jumat', '13.30 - 16.00 WIB', 'Ruang Kelas 3.03 FST', 35, None, 'Anif Hanifa Setianingrum, M.Si', 'Dibuka', 1, 0, 2, '2BTI', 'W'),
    ('NAS6112201', 'Pancasila', 2, 'Senin', '10.30 - 12.10 WIB', 'Ruang Kelas 3.01 FST', 35, None, 'Nurul Faizah Rozy, MTI', 'Dibuka', 1, 0, 2, '2CTI', 'W'),

    # Semester 3
    ('FST6091103', 'Sistem Basis Data', 3, 'Selasa', '08.00 - 10.30 WIB', 'Ruang Teater FST Lt. 2', 35, None, 'Fenty Eka Muzayyana Agustin, M.Kom.', 'Dibuka', 1, 0, 3, '3ATI', 'W'),
    ('FST6091105', 'Organisasi dan Arsitektur Komputer', 4, 'Rabu', '10.30 - 13.50 WIB', 'Lab Hardware Lt. 2', 35, None, 'Muhamad Azhari, S.Kom.,M.Kom', 'Dibuka', 1, 0, 3, '3CTI', 'W'),
    ('FST6091106', 'Jaringan Komputer', 4, 'Kamis', '13.00 - 16.20 WIB', 'Lab Jaringan Lt. 3', 35, 6, 'Feri Fahrianto, M.Sc.,Ph.D', 'Dibuka', 1, 0, 3, '3ATI', 'W'),
    ('FST6091107', 'Struktur Data dan Algoritma', 3, 'Rabu', '08.00 - 10.30 WIB', 'Lab Komputer 2 Lt. 3', 35, None, 'Viva Arifin, MMSI.', 'Dibuka', 1, 0, 3, '3ATI', 'W'),
    ('FST6091108', 'Rekayasa Perangkat Lunak', 3, 'Senin', '08.00 - 10.30 WIB', 'Lab RPL FST Lt. 3', 35, 6, 'Luh Kesuma Wardhani, S.T., M.T.', 'Dibuka', 1, 0, 3, '3ATI', 'W'),
    ('FST6091123', 'Matematika Informatika II', 3, 'Selasa', '10.30 - 13.00 WIB', 'Ruang Kelas 3.02 FST', 35, None, 'Anif Hanifa Setianingrum, M.Si', 'Dibuka', 1, 0, 3, '3BTI', 'W'),
    ('UIN6014203', 'Bahasa Inggris', 3, 'Senin', '10.30 - 13.00 WIB', 'Ruang Kelas 3.04 FST', 35, None, 'Luthfiana Dwi Rakhmawati, S.Pd.,M.A', 'Dibuka', 1, 0, 3, '3ATI', 'W'),

    # Semester 4
    ('FST6091109', 'Pemrograman Web', 3, 'Kamis', '08.00 - 10.30 WIB', 'Lab Komputer 1 Lt. 3', 35, None, 'Hendra Bayu Suseno, M.Kom.', 'Dibuka', 1, 0, 4, '4ATI', 'W'),
    ('FST6091110', 'Sistem Operasi', 3, 'Jumat', '08.00 - 10.30 WIB', 'Ruang Kelas 3.01 FST', 35, None, 'Victor Amrizal, M.Kom.', 'Dibuka', 1, 0, 4, '4BTI', 'W'),
    ('FST6091111', 'Teori Bahasa dan Otomata', 3, 'Senin', '13.00 - 15.30 WIB', 'Ruang Kelas 3.03 FST', 35, None, 'Fitri Mintarsih, M.Kom.', 'Dibuka', 1, 0, 4, '4CTI', 'W'),
    ('FST6091112', 'Analisis dan Desain Algoritma', 3, 'Selasa', '13.00 - 15.30 WIB', 'Ruang Kelas 3.04 FST', 35, None, 'Dr.Imam Marzuki Shofi, M.T.', 'Dibuka', 1, 0, 4, '4DTI', 'W'),

    # Semester 5
    ('FST6091501', 'Pemrograman Berbasis Platform', 3, 'Rabu', '08.00 - 10.30 WIB', 'Lab Komputer 2 Lt. 3', 35, 6, 'Hendra Bayu Suseno, M.Kom.', 'Dibuka', 1, 0, 5, '5ATI', 'W'),
    ('FST6091502', 'Keamanan Informasi', 3, 'Kamis', '08.00 - 10.30 WIB', 'Lab Komputer 2 Lt. 3', 35, None, 'Arini, S.T., M.T.', 'Dibuka', 1, 0, 5, '5ATI', 'W'),
    ('FST6091503', 'Kecerdasan Buatan', 3, 'Senin', '08.00 - 10.30 WIB', 'Ruang Kelas 3.03 FST', 35, None, 'Victor Amrizal, M.Kom.', 'Dibuka', 1, 0, 5, '5BTI', 'W'),
    ('FST6091504', 'Pemodelan Dan Simulasi', 3, 'Rabu', '08.00 - 10.30 WIB', 'Lab Komputer 1 Lt. 3', 35, None, 'Muhamad Azhari, S.Kom.,M.Kom', 'Dibuka', 1, 0, 5, '5ATI', 'W'),
    ('FST6091901', 'Penjaminan Mutu Perangkat Lunak (SQA)', 3, 'Jumat', '13.30 - 16.00 WIB', 'Ruang Kelas 3.04 FST', 33, None, 'Rizal, M.Kom.', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091903', 'Rekayasa pra-syarat (Requirements Engineering)', 3, 'Selasa', '13.00 - 15.30 WIB', 'Ruang Kelas 3.02 FST', 33, None, 'Dr.Imam Marzuki Shofi, M.T.', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091905', 'Rekayasa Perangkat Lunak Lanjut', 3, 'Senin', '10.30 - 13.00 WIB', 'Lab RPL FST Lt. 3', 33, None, 'Rizal, M.Kom.', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091907', 'Infrastruktur Teknologi Informasi', 3, 'Rabu', '13.00 - 15.30 WIB', 'Lab Jaringan Lt. 3', 33, None, 'Muhamad Azhari, S.Kom.,M.Kom', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091908', 'Arsitektur dan Integrasi Enterprise', 3, 'Jumat', '08.00 - 10.30 WIB', 'Ruang Kelas 3.01 FST', 33, 5, 'Andrew Fiade, M.Kom.', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091912', 'Data Science', 3, 'Senin', '13.00 - 15.30 WIB', 'Lab Riset Informatika Lt. 3', 34, 5, 'Siti Ummi Masruroh, M.Sc.', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091917', 'Wireless Sensor Network', 3, 'Kamis', '13.00 - 15.30 WIB', 'Lab Jaringan Lt. 3', 33, None, 'Nurhayati, Ph.D.', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091918', 'Sistem Benam', 3, 'Rabu', '10.30 - 13.00 WIB', 'Lab Hardware Lt. 2', 33, None, 'Dr.Nenny Anggraini, S.Kom, MT', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091926', 'Sistem Basis Data Lanjut', 3, 'Selasa', '10.30 - 13.00 WIB', 'Ruang Teater FST Lt. 2', 30, 5, 'Muhammad Sobri, S.Kom.,M.Kom.,Ph.D', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6093261', 'Etika Profesi Teknologi Informasi', 2, 'Selasa', '08.00 - 09.40 WIB', 'Ruang Kelas 3.02 FST', 35, None, 'Fenty Eka Muzayyana Agustin, M.Kom.', 'Dibuka', 1, 0, 5, '5ATI', 'W'),
    ('UIN6000208', 'Metodologi Penelitian', 3, 'Selasa', '10.30 - 13.00 WIB', 'Ruang Kelas 3.01 FST', 35, None, 'Khodijah Hulliyah, M.Si., Ph.D', 'Dibuka', 1, 0, 5, '5CTI', 'W'),

    # Semester 6
    ('FST6091925', 'Sistem Operasi Lanjut', 3, 'Senin', '13.00 - 15.30 WIB', 'Ruang Kelas 3.01 FST', 33, None, 'Victor Amrizal, M.Kom.', 'Dibuka', 1, 0, 6, '6PTI', 'P'),
    ('FST6091928', 'Kapita Selekta Komputasi', 3, 'Selasa', '13.00 - 15.30 WIB', 'Ruang Teater FST Lt. 2', 30, None, 'Prof.Husni Teja Sukmana, Ph.D', 'Dibuka', 1, 0, 6, '6PTI', 'P'),
]


def _seed_demo_applications(cursor: sqlite3.Cursor) -> None:
    """Seed sample KRS applications for secondary demo students on brand-new DBs."""
    # Student 2 (Danuardi Saputro) -> Diajukan (ready for DPA verification demo)
    danu = cursor.execute("SELECT id FROM users WHERE username = '1251420128'").fetchone()
    revand = cursor.execute("SELECT id FROM users WHERE username = '1251420017'").fetchone()
    c_rpl = cursor.execute("SELECT id, sks FROM courses WHERE code = 'FST6091108'").fetchone()
    c_sbd = cursor.execute("SELECT id, sks FROM courses WHERE code = 'FST6091103'").fetchone()
    c_pbp = cursor.execute("SELECT id, sks FROM courses WHERE code = 'FST6091501'").fetchone()
    c_jar = cursor.execute("SELECT id, sks FROM courses WHERE code = 'FST6091106'").fetchone()

    if danu and c_rpl and c_sbd:
        total = c_rpl['sks'] + c_sbd['sks']
        cursor.execute(
            '''
            INSERT INTO krs_applications (student_id, semester_period, total_sks, status)
            VALUES (?, 'Semester Antara 2026/2027', ?, 'Diajukan')
            ''',
            (danu['id'], total),
        )
        app_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO krs_items (application_id, course_id, status) VALUES (?, ?, 'Aktif')",
            (app_id, c_rpl['id']),
        )
        cursor.execute(
            "INSERT INTO krs_items (application_id, course_id, status) VALUES (?, ?, 'Aktif')",
            (app_id, c_sbd['id']),
        )

    if revand and c_pbp and c_jar:
        total = c_pbp['sks'] + c_jar['sks']
        cursor.execute(
            '''
            INSERT INTO krs_applications (student_id, semester_period, total_sks, status, verified_at)
            VALUES (?, 'Semester Antara 2026/2027', ?, 'Lunas', CURRENT_TIMESTAMP)
            ''',
            (revand['id'], total),
        )
        app_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO krs_items (application_id, course_id, status) VALUES (?, ?, 'Aktif')",
            (app_id, c_pbp['id']),
        )
        cursor.execute(
            "INSERT INTO krs_items (application_id, course_id, status) VALUES (?, ?, 'Aktif')",
            (app_id, c_jar['id']),
        )
        cursor.execute(
            '''
            INSERT INTO invoices (application_id, student_id, va_number, bank_name, amount, status, paid_at, payment_channel, reconciliation_notes)
            VALUES (?, ?, '88714200178205', 'Bank Mandiri', ?, 'Lunas', CURRENT_TIMESTAMP, 'Rekonsiliasi Manual Bank', 'Ref: ATM-PAY-DEMO-01 | Pembayaran Demo Awal')
            ''',
            (app_id, revand['id'], total * 220000),
        )


def seed_initial_data(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    for key, value in DEFAULT_CONFIGS:
        cursor.execute(
            "INSERT OR IGNORE INTO system_config (key, value) VALUES (?, ?)",
            (key, value),
        )

    users_count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    is_fresh_users = users_count == 0
    if is_fresh_users:
        cursor.executemany(
            '''
            INSERT OR IGNORE INTO users (username, password, name, nim_nip, role, prodi, ipk, semester, dpa_id, avatar)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            SEED_USERS,
        )

    courses_count = cursor.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    if courses_count == 0:
        cursor.executemany(
            '''
            INSERT OR IGNORE INTO courses (
                code, name, sks, schedule_day, schedule_time, room, quota,
                lecturer_id, lecturer_name, status, lecturer_agreed,
                lecturer_dispensation_agreed, semester, class_name, wp_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            SEED_COURSES,
        )

    apps_count = cursor.execute("SELECT COUNT(*) FROM krs_applications").fetchone()[0]
    if is_fresh_users and apps_count == 0:
        _seed_demo_applications(cursor)
