from werkzeug.security import generate_password_hash

DEFAULT_CONFIGS = [
    ('registration_status', 'Buka'),
    ('registration_start', '2026-07-01'),
    ('registration_end', '2026-07-25'),
    ('sks_rate', '220000'),
    ('active_semester', 'Semester Antara 2026/2027'),
    ('max_sks', '9'),
    ('min_quota', '10'),
]

# 5 Akun Demo Utama + Mahasiswa Pendukung untuk Data Simulasi
# Format: (username, raw_password, name, nim_nip, role, prodi, ipk, semester, dpa_id, avatar, email, is_active)
SEED_USERS = [
    # 5 Akun Demo Utama sesuai RBAC
    ('1084729301', 'mhs123', 'IHSAN MUBAROK', '1084729301', 'mahasiswa', 'Teknik Informatika', 3.75, 6, None, '25110120414.png', 'mahasiswa@uinjkt.ac.id', 1),
    ('dosen1', 'dosen123', 'Luh Kesuma Wardhani, S.T., M.T.', '198003152006042002', 'dosen', 'Teknik Informatika', 0.0, 0, None, None, 'dosen@uinjkt.ac.id', 1),
    ('kaprodi', 'kaprodi123', 'Dr. Dewi Khairani, M.Sc.', '197805122005012001', 'kaprodi', 'Teknik Informatika', 0.0, 0, None, None, 'kaprodi@uinjkt.ac.id', 1),
    ('admin_tu', 'admin123', 'Admin Akademik & TU FST', 'ADMIN-TU-FST-01', 'admin_akademik', 'Fakultas Sains dan Teknologi', 0.0, 0, None, None, 'admin.tu@uinjkt.ac.id', 1),
    ('superadmin', 'superadmin123', 'Super Administrator Sistem', 'SUPERADMIN-01', 'superadmin', 'Universitas', 0.0, 0, None, None, 'superadmin@uinjkt.ac.id', 1),

    # Mahasiswa tambahan untuk data simulasi pengajuan di dasbor Dosen/Kaprodi/Admin
    ('1093847152', 'mhs123', 'DANUARDI SAPUTRO', '1093847152', 'mahasiswa', 'Teknik Informatika', 3.65, 6, None, '25110120414.png', 'danuardi@uinjkt.ac.id', 1),
    ('1072918463', 'mhs123', 'MUHAMMAD BAGAS F', '1072918463', 'mahasiswa', 'Teknik Informatika', 3.42, 6, None, '25110120414.png', 'bagas@uinjkt.ac.id', 1),
    ('1065829174', 'mhs123', 'REVAND RADITIYA D', '1065829174', 'mahasiswa', 'Teknik Informatika', 3.58, 6, None, '25110120414.png', 'revand@uinjkt.ac.id', 1),
]

DEMO_ACCOUNTS_INFO = [
    {
        'label': 'Mahasiswa',
        'role': 'mahasiswa',
        'username': '1084729301',
        'email': 'mahasiswa@uinjkt.ac.id',
        'password': 'mhs123',
        'desc': 'Mengajukan KRS semester antara & memantau status pengajuan sendiri',
    },
    {
        'label': 'Dosen Pengampu',
        'role': 'dosen',
        'username': 'dosen1',
        'email': 'dosen@uinjkt.ac.id',
        'password': 'dosen123',
        'desc': 'Melihat mata kuliah & pengajuan terkait serta memberi persetujuan/catatan akademik',
    },
    {
        'label': 'Kaprodi / Koordinator',
        'role': 'kaprodi',
        'username': 'kaprodi',
        'email': 'kaprodi@uinjkt.ac.id',
        'password': 'kaprodi123',
        'desc': 'Memverifikasi seluruh pengajuan, mengelola jadwal/kelas, & melihat rekap',
    },
    {
        'label': 'Admin Akademik / TU',
        'role': 'admin_akademik',
        'username': 'admin_tu',
        'email': 'admin.tu@uinjkt.ac.id',
        'password': 'admin123',
        'desc': 'Mengelola data master (mahasiswa, dosen, MK) & memproses administrasi pengajuan',
    },
    {
        'label': 'Super Admin',
        'role': 'superadmin',
        'username': 'superadmin',
        'email': 'superadmin@uinjkt.ac.id',
        'password': 'superadmin123',
        'desc': 'Akses penuh ke seluruh menu sistem dan manajemen pengguna',
    },
]

# Full 45-course catalog for Paket Semester 1 s.d. 6 (Program Studi Teknik Informatika UIN Jakarta)
SEED_COURSES = [
    # Semester 1
    ('FST6091101', 'Dasar-dasar Pemrograman', 3, 'Senin', '08.00 - 10.30 WIB', 'Lab Komputer 1 Lt. 3', 33, 'dosen1', 'Luh Kesuma Wardhani, S.T., M.T.', 'Dibuka', 1, 0, 1, '1ATI', 'W'),
    ('FST6091125', 'Elektronika Dasar', 3, 'Selasa', '08.00 - 10.30 WIB', 'Lab Hardware Lt. 2', 33, None, 'Feri Fahrianto, M.Sc.,Ph.D', 'Dibuka', 1, 0, 1, '1BTI', 'W'),
    ('FST6091201', 'Literasi Digital', 2, 'Rabu', '08.00 - 09.40 WIB', 'Ruang Teater FST Lt. 2', 33, None, 'Victor Amrizal, M.Kom.', 'Dibuka', 1, 0, 1, '1CTI', 'W'),
    ('FST6094102', 'Matematika Diskrit', 4, 'Kamis', '08.00 - 11.20 WIB', 'Ruang Kelas 3.01 FST', 33, None, 'Luh Kesuma Wardhani, S.T., M.T.', 'Dibuka', 1, 0, 1, '1DTI', 'W'),
    ('NAS6112203', 'Pendidikan Kewarganegaraan', 2, 'Jumat', '08.00 - 09.40 WIB', 'Ruang Kelas 3.02 FST', 33, None, 'Nurul Faizah Rozy, MTI', 'Dibuka', 1, 0, 1, '1ETI', 'W'),
    ('UIN6032205', 'Praktikum Qira’ah dan Ibadah', 2, 'Senin', '13.00 - 14.40 WIB', 'Masjid FST Lt. 1', 33, None, 'Drs.M. Tabah Rosyadi, M.A.', 'Dibuka', 1, 0, 1, '1ATI', 'W'),
    ('UIN6033201', 'Studi Islam', 4, 'Selasa', '13.00 - 16.20 WIB', 'Ruang Teater FST Lt. 2', 33, None, 'Burhanuddin, M.A.', 'Dibuka', 1, 0, 1, '1BTI', 'W'),
    ('TIF3101', 'Rekayasa Perangkat Lunak', 3, 'Senin', '08.00 - 10.30 WIB', 'Lab RPL FST Lt. 3', 30, 'dosen1', 'Luh Kesuma Wardhani, S.T., M.T.', 'Dibuka', 1, 0, 1, '1ATI', 'W'),
    ('TIF3102', 'Basis Data Lanjut', 3, 'Selasa', '10.30 - 13.00 WIB', 'Ruang Teater FST Lt. 2', 25, 'kaprodi', 'Dr. Dewi Khairani, M.Sc.', 'Dibuka', 1, 0, 1, '1ATI', 'W'),
    ('TIF3103', 'Pemrograman Berorientasi Objek', 3, 'Rabu', '08.00 - 10.30 WIB', 'Lab Komputer 2 Lt. 3', 30, 'dosen1', 'Luh Kesuma Wardhani, S.T., M.T.', 'Dibuka', 1, 0, 1, '1ATI', 'W'),
    ('TIF3104', 'Jaringan Komputer', 3, 'Kamis', '13.00 - 15.30 WIB', 'Lab Jaringan Lt. 3', 25, 'dosen1', 'Luh Kesuma Wardhani, S.T., M.T.', 'Menunggu', 0, 0, 1, '1ATI', 'W'),
    ('TIF3105', 'Sistem Informasi Enterprise', 3, 'Jumat', '08.00 - 10.30 WIB', 'Ruang Kelas 3.01 FST', 15, 'kaprodi', 'Dr. Dewi Khairani, M.Sc.', 'Menunggu', 1, 0, 1, '1ATI', 'W'),
    ('TIF3106', 'Pengolahan Citra Digital', 3, 'Senin', '13.00 - 15.30 WIB', 'Ruang Kelas 3.02 FST', 20, 'kaprodi', 'Dr. Dewi Khairani, M.Sc.', 'Menunggu', 0, 0, 1, '1ATI', 'W'),

    # Semester 2
    ('UIN6033205', 'Praktikum Qira’ah dan Ibadah', 2, 'Rabu', '13.00 - 14.40 WIB', 'Masjid FST Lt. 1', 10, None, 'Drs.M. Tabah Rosyadi, M.A.', 'Dibuka', 1, 0, 2, '120TI', 'W'),
    ('FST6091102', 'Algoritma dan Pemrograman Lanjut', 3, 'Kamis', '13.00 - 15.30 WIB', 'Lab Komputer 2 Lt. 3', 35, None, 'Nurhayati, Ph.D.', 'Dibuka', 1, 0, 2, '2ATI', 'W'),
    ('FST6091104', 'Matematika Informatika I', 3, 'Jumat', '13.30 - 16.00 WIB', 'Ruang Kelas 3.03 FST', 35, None, 'Anif Hanifa Setianingrum, M.Si', 'Dibuka', 1, 0, 2, '2BTI', 'W'),
    ('NAS6112201', 'Pancasila', 2, 'Senin', '10.30 - 12.10 WIB', 'Ruang Kelas 3.01 FST', 35, None, 'Nurul Faizah Rozy, MTI', 'Dibuka', 1, 0, 2, '2CTI', 'W'),

    # Semester 3
    ('FST6091103', 'Sistem Basis Data', 3, 'Selasa', '08.00 - 10.30 WIB', 'Ruang Teater FST Lt. 2', 35, None, 'Fenty Eka Muzayyana Agustin, M.Kom.', 'Dibuka', 1, 0, 3, '3ATI', 'W'),
    ('FST6091105', 'Organisasi dan Arsitektur Komputer', 4, 'Rabu', '10.30 - 13.50 WIB', 'Lab Hardware Lt. 2', 35, None, 'Muhamad Azhari, S.Kom.,M.Kom', 'Dibuka', 1, 0, 3, '3CTI', 'W'),
    ('FST6091106', 'Jaringan Komputer', 4, 'Kamis', '13.00 - 16.20 WIB', 'Lab Jaringan Lt. 3', 35, 'dosen1', 'Feri Fahrianto, M.Sc.,Ph.D', 'Dibuka', 1, 0, 3, '3ATI', 'W'),
    ('FST6091107', 'Struktur Data dan Algoritma', 3, 'Rabu', '08.00 - 10.30 WIB', 'Lab Komputer 2 Lt. 3', 35, None, 'Viva Arifin, MMSI.', 'Dibuka', 1, 0, 3, '3ATI', 'W'),
    ('FST6091108', 'Rekayasa Perangkat Lunak', 3, 'Senin', '08.00 - 10.30 WIB', 'Lab RPL FST Lt. 3', 35, 'dosen1', 'Luh Kesuma Wardhani, S.T., M.T.', 'Dibuka', 1, 0, 3, '3ATI', 'W'),
    ('FST6091123', 'Matematika Informatika II', 3, 'Selasa', '10.30 - 13.00 WIB', 'Ruang Kelas 3.02 FST', 35, None, 'Anif Hanifa Setianingrum, M.Si', 'Dibuka', 1, 0, 3, '3BTI', 'W'),
    ('UIN6014203', 'Bahasa Inggris', 3, 'Senin', '10.30 - 13.00 WIB', 'Ruang Kelas 3.04 FST', 35, None, 'Luthfiana Dwi Rakhmawati, S.Pd.,M.A', 'Dibuka', 1, 0, 3, '3ATI', 'W'),

    # Semester 4
    ('FST6091109', 'Pemrograman Web', 3, 'Kamis', '08.00 - 10.30 WIB', 'Lab Komputer 1 Lt. 3', 35, None, 'Hendra Bayu Suseno, M.Kom.', 'Dibuka', 1, 0, 4, '4ATI', 'W'),
    ('FST6091110', 'Sistem Operasi', 3, 'Jumat', '08.00 - 10.30 WIB', 'Ruang Kelas 3.01 FST', 35, None, 'Victor Amrizal, M.Kom.', 'Dibuka', 1, 0, 4, '4BTI', 'W'),
    ('FST6091111', 'Teori Bahasa dan Otomata', 3, 'Senin', '13.00 - 15.30 WIB', 'Ruang Kelas 3.03 FST', 35, None, 'Fitri Mintarsih, M.Kom.', 'Dibuka', 1, 0, 4, '4CTI', 'W'),
    ('FST6091112', 'Analisis dan Desain Algoritma', 3, 'Selasa', '13.00 - 15.30 WIB', 'Ruang Kelas 3.04 FST', 35, None, 'Dr.Imam Marzuki Shofi, M.T.', 'Dibuka', 1, 0, 4, '4DTI', 'W'),

    # Semester 5
    ('FST6091501', 'Pemrograman Berbasis Platform', 3, 'Rabu', '08.00 - 10.30 WIB', 'Lab Komputer 2 Lt. 3', 35, 'dosen1', 'Hendra Bayu Suseno, M.Kom.', 'Dibuka', 1, 0, 5, '5ATI', 'W'),
    ('FST6091502', 'Keamanan Informasi', 3, 'Kamis', '08.00 - 10.30 WIB', 'Lab Komputer 2 Lt. 3', 35, None, 'Arini, S.T., M.T.', 'Dibuka', 1, 0, 5, '5ATI', 'W'),
    ('FST6091503', 'Kecerdasan Buatan', 3, 'Senin', '08.00 - 10.30 WIB', 'Ruang Kelas 3.03 FST', 35, None, 'Victor Amrizal, M.Kom.', 'Dibuka', 1, 0, 5, '5BTI', 'W'),
    ('FST6091504', 'Pemodelan Dan Simulasi', 3, 'Rabu', '08.00 - 10.30 WIB', 'Lab Komputer 1 Lt. 3', 35, None, 'Muhamad Azhari, S.Kom.,M.Kom', 'Dibuka', 1, 0, 5, '5ATI', 'W'),
    ('FST6091901', 'Penjaminan Mutu Perangkat Lunak (SQA)', 3, 'Jumat', '13.30 - 16.00 WIB', 'Ruang Kelas 3.04 FST', 33, None, 'Rizal, M.Kom.', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091903', 'Rekayasa pra-syarat (Requirements Engineering)', 3, 'Selasa', '13.00 - 15.30 WIB', 'Ruang Kelas 3.02 FST', 33, None, 'Dr.Imam Marzuki Shofi, M.T.', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091905', 'Rekayasa Perangkat Lunak Lanjut', 3, 'Senin', '10.30 - 13.00 WIB', 'Lab RPL FST Lt. 3', 33, None, 'Rizal, M.Kom.', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091907', 'Infrastruktur Teknologi Informasi', 3, 'Rabu', '13.00 - 15.30 WIB', 'Lab Jaringan Lt. 3', 33, None, 'Muhamad Azhari, S.Kom.,M.Kom', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091908', 'Arsitektur dan Integrasi Enterprise', 3, 'Jumat', '08.00 - 10.30 WIB', 'Ruang Kelas 3.01 FST', 33, 'kaprodi', 'Andrew Fiade, M.Kom.', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091912', 'Data Science', 3, 'Senin', '13.00 - 15.30 WIB', 'Lab Riset Informatika Lt. 3', 34, 'kaprodi', 'Siti Ummi Masruroh, M.Sc.', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091917', 'Wireless Sensor Network', 3, 'Kamis', '13.00 - 15.30 WIB', 'Lab Jaringan Lt. 3', 33, None, 'Nurhayati, Ph.D.', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091918', 'Sistem Benam', 3, 'Rabu', '10.30 - 13.00 WIB', 'Lab Hardware Lt. 2', 33, None, 'Dr.Nenny Anggraini, S.Kom, MT', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6091926', 'Sistem Basis Data Lanjut', 3, 'Selasa', '10.30 - 13.00 WIB', 'Ruang Teater FST Lt. 2', 30, 'kaprodi', 'Muhammad Sobri, S.Kom.,M.Kom.,Ph.D', 'Dibuka', 1, 0, 5, '5PTI', 'P'),
    ('FST6093261', 'Etika Profesi Teknologi Informasi', 2, 'Selasa', '08.00 - 09.40 WIB', 'Ruang Kelas 3.02 FST', 35, None, 'Fenty Eka Muzayyana Agustin, M.Kom.', 'Dibuka', 1, 0, 5, '5ATI', 'W'),
    ('UIN6000208', 'Metodologi Penelitian', 3, 'Selasa', '10.30 - 13.00 WIB', 'Ruang Kelas 3.01 FST', 35, None, 'Khodijah Hulliyah, M.Si., Ph.D', 'Dibuka', 1, 0, 5, '5CTI', 'W'),

    # Semester 6
    ('FST6091925', 'Sistem Operasi Lanjut', 3, 'Senin', '13.00 - 15.30 WIB', 'Ruang Kelas 3.01 FST', 33, None, 'Victor Amrizal, M.Kom.', 'Dibuka', 1, 0, 6, '6PTI', 'P'),
    ('FST6091928', 'Kapita Selekta Komputasi', 3, 'Selasa', '13.00 - 15.30 WIB', 'Ruang Teater FST Lt. 2', 30, None, 'Prof.Husni Teja Sukmana, Ph.D', 'Dibuka', 1, 0, 6, '6PTI', 'P'),
]


def _seed_demo_applications(conn) -> None:
    """Seed sample KRS applications for secondary demo students on brand-new DBs."""
    danu = conn.execute("SELECT id FROM users WHERE username = '1093847152'").fetchone()
    revand = conn.execute("SELECT id FROM users WHERE username = '1065829174'").fetchone()
    c_rpl = conn.execute("SELECT id, sks FROM courses WHERE code = 'FST6091108'").fetchone()
    c_sbd = conn.execute("SELECT id, sks FROM courses WHERE code = 'FST6091103'").fetchone()
    c_pbp = conn.execute("SELECT id, sks FROM courses WHERE code = 'FST6091501'").fetchone()
    c_jar = conn.execute("SELECT id, sks FROM courses WHERE code = 'FST6091106'").fetchone()

    if danu and c_rpl and c_sbd:
        total = c_rpl['sks'] + c_sbd['sks']
        app_id = conn.insert_returning_id(
            '''
            INSERT INTO krs_applications (student_id, semester_period, total_sks, status)
            VALUES (?, 'Semester Antara 2026/2027', ?, 'Diajukan')
            ''',
            (danu['id'], total),
        )
        conn.execute(
            "INSERT INTO krs_items (application_id, course_id, status) VALUES (?, ?, 'Aktif')",
            (app_id, c_rpl['id']),
        )
        conn.execute(
            "INSERT INTO krs_items (application_id, course_id, status) VALUES (?, ?, 'Aktif')",
            (app_id, c_sbd['id']),
        )

    if revand and c_pbp and c_jar:
        total = c_pbp['sks'] + c_jar['sks']
        app_id = conn.insert_returning_id(
            '''
            INSERT INTO krs_applications (
                student_id, semester_period, total_sks, status,
                lecturer_approval, lecturer_notes, verified_at
            )
            VALUES (
                ?, 'Semester Antara 2026/2027', ?, 'Lunas',
                'Disetujui', 'Memenuhi syarat akademik mata kuliah.', CURRENT_TIMESTAMP
            )
            ''',
            (revand['id'], total),
        )
        conn.execute(
            "INSERT INTO krs_items (application_id, course_id, status) VALUES (?, ?, 'Aktif')",
            (app_id, c_pbp['id']),
        )
        conn.execute(
            "INSERT INTO krs_items (application_id, course_id, status) VALUES (?, ?, 'Aktif')",
            (app_id, c_jar['id']),
        )
        conn.execute(
            '''
            INSERT INTO invoices (
                application_id, student_id, va_number, bank_name, amount, status,
                paid_at, payment_channel, reconciliation_notes
            )
            VALUES (
                ?, ?, '88718291748205', 'Bank Mandiri', ?, 'Lunas',
                CURRENT_TIMESTAMP, 'Rekonsiliasi Manual Bank', 'Ref: ATM-PAY-DEMO-01 | Pembayaran Demo Awal'
            )
            ON CONFLICT (application_id) DO NOTHING
            ''',
            (app_id, revand['id'], total * 220000),
        )


LEGACY_STUDENT_NAME_TO_NIM = {
    'IHSAN MUBAROK': '1084729301',
    'DANUARDI SAPUTRO': '1093847152',
    'MUHAMMAD BAGAS F': '1072918463',
    'REVAND RADITIYA D': '1065829174',
}


def _ensure_rbac_demo_accounts(conn) -> None:
    """Ensure all 5 RBAC demo accounts and hashed passwords exist even on migrated DBs."""
    legacy_rows = conn.execute(
        "SELECT id, name FROM users WHERE role = 'mahasiswa' AND username LIKE '1251420%'"
    ).fetchall()
    for row in legacy_rows:
        target_nim = LEGACY_STUDENT_NAME_TO_NIM.get(row['name'])
        if not target_nim:
            continue
        exists_new = conn.execute("SELECT id FROM users WHERE username = ?", (target_nim,)).fetchone()
        if not exists_new:
            conn.execute(
                "UPDATE users SET username = ?, nim_nip = ? WHERE id = ?",
                (target_nim, target_nim, row['id']),
            )

    for username, raw_pw, name, nim_nip, role, prodi, ipk, sem, dpa_id, avatar, email, is_active in SEED_USERS:
        existing = conn.execute(
            "SELECT id, password, email FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not existing:
            conn.execute(
                '''
                INSERT INTO users (
                    username, password, name, nim_nip, role, prodi, ipk, semester, dpa_id, avatar, email, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (username) DO NOTHING
                ''',
                (
                    username,
                    generate_password_hash(raw_pw),
                    name,
                    nim_nip,
                    role,
                    prodi,
                    ipk,
                    sem,
                    dpa_id,
                    avatar,
                    email,
                    is_active,
                ),
            )
        else:
            updates = []
            params = []
            if not existing['email'] and email:
                updates.append("email = ?")
                params.append(email)
            # Upgrade legacy plain default password '123456' to hashed demo password
            if existing['password'] == '123456':
                updates.append("password = ?")
                params.append(generate_password_hash(raw_pw))
            if updates:
                params.append(existing['id'])
                conn.execute(
                    f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                    tuple(params),
                )

    # Normalize legacy role names on older DBs if present
    conn.execute("UPDATE users SET role = 'kaprodi' WHERE role = 'prodi'")
    conn.execute("UPDATE users SET role = 'admin_akademik' WHERE role = 'keuangan'")
    conn.execute("UPDATE users SET role = 'dosen' WHERE role = 'dpa'")

    kaprodi_row = conn.execute("SELECT id FROM users WHERE username = 'kaprodi'").fetchone()
    if kaprodi_row:
        conn.execute(
            "UPDATE users SET dpa_id = ? WHERE role = 'mahasiswa' AND dpa_id IS NULL",
            (kaprodi_row['id'],),
        )


def seed_initial_data(conn) -> None:
    for key, value in DEFAULT_CONFIGS:
        conn.execute(
            "INSERT INTO system_config (key, value) VALUES (?, ?) ON CONFLICT (key) DO NOTHING",
            (key, value),
        )

    users_count = conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()['cnt']
    is_fresh_users = users_count == 0
    _ensure_rbac_demo_accounts(conn)

    courses_count = conn.execute("SELECT COUNT(*) AS cnt FROM courses").fetchone()['cnt']
    if courses_count == 0:
        user_id_by_username = {
            row['username']: row['id']
            for row in conn.execute(
                "SELECT id, username FROM users WHERE username IN ('kaprodi', 'dosen1')"
            ).fetchall()
        }
        resolved_courses = [
            (
                code, name, sks, day, time_str, room, quota,
                user_id_by_username.get(lecturer_ref) if lecturer_ref else None,
                lecturer_name, status, agreed, disp_agreed, semester, class_name, wp_type,
            )
            for (
                code, name, sks, day, time_str, room, quota,
                lecturer_ref, lecturer_name, status, agreed, disp_agreed,
                semester, class_name, wp_type,
            ) in SEED_COURSES
        ]
        conn.executemany(
            '''
            INSERT INTO courses (
                code, name, sks, schedule_day, schedule_time, room, quota,
                lecturer_id, lecturer_name, status, lecturer_agreed,
                lecturer_dispensation_agreed, semester, class_name, wp_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (code) DO NOTHING
            ''',
            resolved_courses,
        )

    apps_count = conn.execute("SELECT COUNT(*) AS cnt FROM krs_applications").fetchone()['cnt']
    if is_fresh_users and apps_count == 0:
        _seed_demo_applications(conn)
