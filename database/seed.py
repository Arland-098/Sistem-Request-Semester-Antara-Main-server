from werkzeug.security import generate_password_hash

DEFAULT_CONFIGS = [
    ('registration_status', 'Buka'),
    ('proposal_start', '2026-06-20'),
    ('proposal_end', '2026-06-30'),
    ('registration_start', '2026-07-01'),
    ('registration_end', '2026-07-25'),
    ('payment_start', '2026-07-26'),
    ('payment_end', '2026-08-05'),
    ('sks_rate', '220000'),
    ('sks_rate_kesehatan', '850000'),
    ('active_semester', 'Semester Antara 2026/2027'),
    ('max_sks', '9'),
    ('min_quota', '10'),
]

SEED_PROGRAMS = [
    ('60', 'Teknik Informatika', 'Fakultas Sains dan Teknologi', 'Sarjana Reguler', 'Menyelenggarakan'),
    ('55', 'Sistem Informasi', 'Fakultas Sains dan Teknologi', 'Sarjana Reguler', 'Menyelenggarakan'),
    ('56', 'Matematika', 'Fakultas Sains dan Teknologi', 'Sarjana Reguler', 'Menyelenggarakan'),
    ('9', 'Kimia', 'Fakultas Sains dan Teknologi', 'Sarjana Reguler', 'Menyelenggarakan'),
    ('31', 'Fisika', 'Fakultas Sains dan Teknologi', 'Sarjana Reguler', 'Menyelenggarakan'),
    ('17', 'Biologi', 'Fakultas Sains dan Teknologi', 'Sarjana Reguler', 'Menyelenggarakan'),
    ('15', 'Teknik Pertambangan', 'Fakultas Sains dan Teknologi', 'Sarjana Reguler', 'Menyelenggarakan'),
    ('94', 'Teknologi Informasi (S2)', 'Fakultas Sains dan Teknologi', 'Sarjana Reguler', 'Menyelenggarakan'),
    ('70', 'Pendidikan Dokter', 'Fakultas Kedokteran', 'Ilmu Kesehatan', 'Menyelenggarakan'),
]

# Format:
# (username, raw_password, name, nim_nip, role, prodi, prodi_code, ipk, semester, status_sanksi, avatar, email, is_active)
SEED_USERS = [
    # 6 Akun Demo Utama (5 Aktor Resmi PDF + Super Admin)
    ('1084729301', 'mhs123', 'IHSAN MUBAROK', '1084729301', 'mahasiswa', 'Teknik Informatika', '60', 3.75, 6, 'Aktif Bebas Sanksi', '25110120414.png', 'mahasiswa@uinjkt.ac.id', 1),
    ('dpa1', 'dpa123', 'Anif Hanifa Setianingrum, M.Si.', '197904102006042001', 'dpa', 'Teknik Informatika', '60', 0.0, 0, 'Aktif Bebas Sanksi', None, 'dpa@uinjkt.ac.id', 1),
    ('dosen1', 'dosen123', 'Luh Kesuma Wardhani, S.T., M.T.', '198003152006042002', 'dosen', 'Teknik Informatika', '60', 0.0, 0, 'Aktif Bebas Sanksi', None, 'dosen@uinjkt.ac.id', 1),
    ('prodi', 'prodi123', 'Dr. Dewi Khairani, M.Sc.', '197805122005012001', 'prodi', 'Teknik Informatika', '60', 0.0, 0, 'Aktif Bebas Sanksi', None, 'prodi@uinjkt.ac.id', 1),
    ('keuangan', 'keuangan123', 'Biro Perencanaan & Keuangan UIN', 'KEUANGAN-BPK-01', 'keuangan', 'Biro Perencanaan & Keuangan', '60', 0.0, 0, 'Aktif Bebas Sanksi', None, 'keuangan@uinjkt.ac.id', 1),
    ('superadmin', 'superadmin123', 'Super Administrator Sistem', 'SUPERADMIN-01', 'superadmin', 'Universitas', '60', 0.0, 0, 'Aktif Bebas Sanksi', None, 'superadmin@uinjkt.ac.id', 1),

    # Mahasiswa tambahan untuk simulasi alur DPA, Prodi (kuota >= 10), Keuangan, & SK Rektor 686/2025
    ('1093847152', 'mhs123', 'DANUARDI SAPUTRO', '1093847152', 'mahasiswa', 'Teknik Informatika', '60', 3.65, 6, 'Aktif Bebas Sanksi', '25110120414.png', 'danuardi@uinjkt.ac.id', 1),
    ('1072918463', 'mhs123', 'MUHAMMAD BAGAS F', '1072918463', 'mahasiswa', 'Teknik Informatika', '60', 2.85, 6, 'Aktif Bebas Sanksi', '25110120414.png', 'bagas@uinjkt.ac.id', 1),
    ('1065829174', 'mhs123', 'REVAND RADITIYA D', '1065829174', 'mahasiswa', 'Teknik Informatika', '60', 3.58, 6, 'Aktif Bebas Sanksi', '25110120414.png', 'revand@uinjkt.ac.id', 1),
    ('1051900001', 'mhs123', 'AHMAD FAUZAN', '1051900001', 'mahasiswa', 'Teknik Informatika', '60', 3.40, 6, 'Aktif Bebas Sanksi', '25110120414.png', 'fauzan@uinjkt.ac.id', 1),
    ('1051900002', 'mhs123', 'SITI RAHMAWATI', '1051900002', 'mahasiswa', 'Teknik Informatika', '60', 3.52, 6, 'Aktif Bebas Sanksi', '25110120414.png', 'rahmawati@uinjkt.ac.id', 1),
    ('1051900003', 'mhs123', 'BUDI SANTOSO', '1051900003', 'mahasiswa', 'Teknik Informatika', '60', 3.21, 5, 'Aktif Bebas Sanksi', '25110120414.png', 'budi@uinjkt.ac.id', 1),
    ('1051900004', 'mhs123', 'NADIA PUTRI', '1051900004', 'mahasiswa', 'Teknik Informatika', '60', 3.68, 6, 'Aktif Bebas Sanksi', '25110120414.png', 'nadia@uinjkt.ac.id', 1),
    ('1051900005', 'mhs123', 'RIZKY PRATAMA', '1051900005', 'mahasiswa', 'Teknik Informatika', '60', 3.15, 4, 'Aktif Bebas Sanksi', '25110120414.png', 'rizky@uinjkt.ac.id', 1),
    ('1051900006', 'mhs123', 'AULIA KHAIRUNNISA', '1051900006', 'mahasiswa', 'Teknik Informatika', '60', 3.44, 6, 'Aktif Bebas Sanksi', '25110120414.png', 'aulia@uinjkt.ac.id', 1),
    ('1051900007', 'mhs123', 'FAJAR NUGROHO', '1051900007', 'mahasiswa', 'Teknik Informatika', '60', 3.10, 5, 'Aktif Bebas Sanksi', '25110120414.png', 'fajar@uinjkt.ac.id', 1),
    ('1051900008', 'mhs123', 'DINDA LESTARI', '1051900008', 'mahasiswa', 'Teknik Informatika', '60', 3.35, 6, 'Aktif Bebas Sanksi', '25110120414.png', 'dinda@uinjkt.ac.id', 1),
    ('1051900009', 'mhs123', 'TEGAR WICAKSONO', '1051900009', 'mahasiswa', 'Teknik Informatika', '60', 3.28, 6, 'Aktif Bebas Sanksi', '25110120414.png', 'tegar@uinjkt.ac.id', 1),
    ('1051900010', 'mhs123', 'FARHAN MAULANA', '1051900010', 'mahasiswa', 'Teknik Informatika', '60', 3.48, 6, 'Aktif Bebas Sanksi', '25110120414.png', 'farhan@uinjkt.ac.id', 1),
]

DEMO_ACCOUNTS_INFO = [
    {
        'label': 'Mahasiswa',
        'role': 'mahasiswa',
        'username': '1084729301',
        'email': 'mahasiswa@uinjkt.ac.id',
        'password': 'mhs123',
        'desc': 'Cek katalog & pengumuman, usul MK internal/lintas prodi, isi/ubah KRS, bayar VA & cetak KRS sah',
    },
    {
        'label': 'Dosen PA (DPA)',
        'role': 'dpa',
        'username': 'dpa1',
        'email': 'dpa@uinjkt.ac.id',
        'password': 'dpa123',
        'desc': 'Memeriksa riwayat IPK/SKS/sanksi & menyetujui/menolak KRS mahasiswa bimbingan',
    },
    {
        'label': 'Dosen Pengampu MK',
        'role': 'dosen',
        'username': 'dosen1',
        'email': 'dosen@uinjkt.ac.id',
        'password': 'dosen123',
        'desc': 'Konfirmasi kesediaan mengajar & kelas dispensasi (<10), serta pantau peserta resmi lunas',
    },
    {
        'label': 'Program Studi / Admin Prodi',
        'role': 'prodi',
        'username': 'prodi',
        'email': 'prodi@uinjkt.ac.id',
        'password': 'prodi123',
        'desc': 'Kelola pengumuman, periode, usulan MK & ekuivalensi, katalog MK, jadwal/ruang, evaluasi kuota & rekap',
    },
    {
        'label': 'Bagian Keuangan',
        'role': 'keuangan',
        'username': 'keuangan',
        'email': 'keuangan@uinjkt.ac.id',
        'password': 'keuangan123',
        'desc': 'Atur tarif SKS (Non-Kesehatan/Kesehatan), pantau tagihan VA kelas buka, rekonsiliasi & cek expired',
    },
    {
        'label': 'Super Admin',
        'role': 'superadmin',
        'username': 'superadmin',
        'email': 'superadmin@uinjkt.ac.id',
        'password': 'superadmin123',
        'desc': 'Akses penuh ke seluruh fitur sistem, manajemen pengguna/RBAC, serta data master',
    },
]

# 45 MK Teknik Informatika ('60') + MK Sistem Informasi ('55') + 1 MK Kedokteran ('70')
# Format: (code, name, sks, day, time_str, room, quota, lecturer_ref, lecturer_name, status, agreed, disp_agreed, disp_req, semester, class_name, wp_type, prodi_code, prodi_name)
SEED_COURSES = [
    # --- SEMESTER 1 (TI) ---
    ('FST6091101', 'Dasar-dasar Pemrograman', 3, 'Senin', '08.00 - 10.30 WIB', 'Lab Komputer 1 Lt. 3', 33, 'dosen1', 'Luh Kesuma Wardhani, S.T., M.T.', 'Ditawarkan', 1, 0, 0, 1, '1ATI', 'W', '60', 'Teknik Informatika'),
    ('FST6091125', 'Elektronika Dasar', 3, 'Selasa', '08.00 - 10.30 WIB', 'Lab Hardware Lt. 2', 33, None, 'Feri Fahrianto, M.Sc.,Ph.D', 'Ditawarkan', 1, 0, 0, 1, '1BTI', 'W', '60', 'Teknik Informatika'),
    ('FST6091201', 'Literasi Digital', 2, 'Rabu', '08.00 - 09.40 WIB', 'Ruang Teater FST Lt. 2', 33, None, 'Victor Amrizal, M.Kom.', 'Ditawarkan', 1, 0, 0, 1, '1CTI', 'W', '60', 'Teknik Informatika'),
    ('FST6094102', 'Matematika Diskrit', 4, 'Kamis', '08.00 - 11.20 WIB', 'Ruang Kelas 3.01 FST', 33, 'dosen1', 'Luh Kesuma Wardhani, S.T., M.T.', 'Ditawarkan', 1, 0, 0, 1, '1DTI', 'W', '60', 'Teknik Informatika'),
    ('NAS6112203', 'Pendidikan Kewarganegaraan', 2, 'Jumat', '08.00 - 09.40 WIB', 'Ruang Kelas 3.02 FST', 33, None, 'Nurul Faizah Rozy, MTI', 'Ditawarkan', 1, 0, 0, 1, '1ETI', 'W', '60', 'Teknik Informatika'),
    ('UIN6032205', 'Praktikum Qira’ah dan Ibadah', 2, 'Senin', '13.00 - 14.40 WIB', 'Masjid FST Lt. 1', 33, None, 'Drs.M. Tabah Rosyadi, M.A.', 'Ditawarkan', 1, 0, 0, 1, '1ATI', 'W', '60', 'Teknik Informatika'),
    ('UIN6033201', 'Studi Islam', 4, 'Selasa', '13.00 - 16.20 WIB', 'Ruang Teater FST Lt. 2', 33, None, 'Burhanuddin, M.A.', 'Ditawarkan', 1, 0, 0, 1, '1BTI', 'W', '60', 'Teknik Informatika'),
    ('TIF3101', 'Rekayasa Perangkat Lunak (Paralel)', 3, 'Senin', '08.00 - 10.30 WIB', 'Lab RPL FST Lt. 3', 30, 'dosen1', 'Luh Kesuma Wardhani, S.T., M.T.', 'Ditawarkan', 1, 0, 0, 1, '1ATI', 'W', '60', 'Teknik Informatika'),
    ('TIF3102', 'Basis Data Lanjut (Paralel)', 3, 'Selasa', '10.30 - 13.00 WIB', 'Ruang Teater FST Lt. 2', 25, 'prodi', 'Dr. Dewi Khairani, M.Sc.', 'Ditawarkan', 1, 0, 0, 1, '1ATI', 'W', '60', 'Teknik Informatika'),
    ('TIF3103', 'Pemrograman Berorientasi Objek', 3, 'Rabu', '08.00 - 10.30 WIB', 'Lab Komputer 2 Lt. 3', 30, 'dosen1', 'Luh Kesuma Wardhani, S.T., M.T.', 'Ditawarkan', 1, 0, 0, 1, '1ATI', 'W', '60', 'Teknik Informatika'),
    ('TIF3104', 'Jaringan Komputer (Paralel)', 3, 'Kamis', '13.00 - 15.30 WIB', 'Lab Jaringan Lt. 3', 25, 'dosen1', 'Luh Kesuma Wardhani, S.T., M.T.', 'Menunggu', 0, 0, 0, 1, '1ATI', 'W', '60', 'Teknik Informatika'),
    ('TIF3105', 'Sistem Informasi Enterprise', 3, 'Jumat', '08.00 - 10.30 WIB', 'Ruang Kelas 3.01 FST', 15, 'prodi', 'Dr. Dewi Khairani, M.Sc.', 'Menunggu', 0, 0, 0, 1, '1ATI', 'W', '60', 'Teknik Informatika'),
    ('TIF3106', 'Pengolahan Citra Digital', 3, 'Senin', '13.00 - 15.30 WIB', 'Ruang Kelas 3.02 FST', 20, 'prodi', 'Dr. Dewi Khairani, M.Sc.', 'Menunggu', 0, 0, 0, 1, '1ATI', 'W', '60', 'Teknik Informatika'),

    # --- SEMESTER 2 (TI) ---
    ('UIN6033205', 'Praktikum Qira’ah dan Ibadah II', 2, 'Rabu', '13.00 - 14.40 WIB', 'Masjid FST Lt. 1', 15, None, 'Drs.M. Tabah Rosyadi, M.A.', 'Ditawarkan', 1, 0, 0, 2, '120TI', 'W', '60', 'Teknik Informatika'),
    ('FST6091102', 'Algoritma dan Pemrograman Lanjut', 3, 'Kamis', '13.00 - 15.30 WIB', 'Lab Komputer 2 Lt. 3', 35, None, 'Nurhayati, Ph.D.', 'Ditawarkan', 1, 0, 0, 2, '2ATI', 'W', '60', 'Teknik Informatika'),
    ('FST6091104', 'Matematika Informatika I', 3, 'Jumat', '13.30 - 16.00 WIB', 'Ruang Kelas 3.03 FST', 35, 'dpa1', 'Anif Hanifa Setianingrum, M.Si.', 'Ditawarkan', 1, 0, 0, 2, '2BTI', 'W', '60', 'Teknik Informatika'),
    ('NAS6112201', 'Pancasila', 2, 'Senin', '10.30 - 12.10 WIB', 'Ruang Kelas 3.01 FST', 35, None, 'Nurul Faizah Rozy, MTI', 'Ditawarkan', 1, 0, 0, 2, '2CTI', 'W', '60', 'Teknik Informatika'),

    # --- SEMESTER 3 (TI) ---
    ('FST6091103', 'Sistem Basis Data', 3, 'Selasa', '08.00 - 10.30 WIB', 'Ruang Teater FST Lt. 2', 35, None, 'Fenty Eka Muzayyana Agustin, M.Kom.', 'Ditawarkan', 1, 0, 0, 3, '3ATI', 'W', '60', 'Teknik Informatika'),
    ('FST6091105', 'Organisasi dan Arsitektur Komputer', 4, 'Rabu', '10.30 - 13.50 WIB', 'Lab Hardware Lt. 2', 35, None, 'Muhamad Azhari, S.Kom.,M.Kom', 'Ditawarkan', 1, 0, 0, 3, '3CTI', 'W', '60', 'Teknik Informatika'),
    ('FST6091106', 'Jaringan Komputer', 4, 'Kamis', '13.00 - 16.20 WIB', 'Lab Jaringan Lt. 3', 35, 'dosen1', 'Luh Kesuma Wardhani, S.T., M.T.', 'Ditawarkan', 1, 0, 0, 3, '3ATI', 'W', '60', 'Teknik Informatika'),
    ('FST6091107', 'Struktur Data dan Algoritma', 3, 'Rabu', '08.00 - 10.30 WIB', 'Lab Komputer 2 Lt. 3', 35, None, 'Viva Arifin, MMSI.', 'Ditawarkan', 1, 0, 0, 3, '3ATI', 'W', '60', 'Teknik Informatika'),
    ('FST6091108', 'Rekayasa Perangkat Lunak', 3, 'Senin', '08.00 - 10.30 WIB', 'Lab RPL FST Lt. 3', 35, 'dosen1', 'Luh Kesuma Wardhani, S.T., M.T.', 'Ditawarkan', 1, 0, 0, 3, '3ATI', 'W', '60', 'Teknik Informatika'),
    ('FST6091123', 'Matematika Informatika II', 3, 'Selasa', '10.30 - 13.00 WIB', 'Ruang Kelas 3.02 FST', 35, 'dpa1', 'Anif Hanifa Setianingrum, M.Si.', 'Ditawarkan', 1, 0, 0, 3, '3BTI', 'W', '60', 'Teknik Informatika'),
    ('UIN6014203', 'Bahasa Inggris', 3, 'Senin', '10.30 - 13.00 WIB', 'Ruang Kelas 3.04 FST', 35, None, 'Luthfiana Dwi Rakhmawati, S.Pd.,M.A', 'Ditawarkan', 1, 0, 0, 3, '3ATI', 'W', '60', 'Teknik Informatika'),

    # --- SEMESTER 4 (TI) ---
    ('FST6091109', 'Pemrograman Web', 3, 'Kamis', '08.00 - 10.30 WIB', 'Lab Komputer 1 Lt. 3', 35, None, 'Hendra Bayu Suseno, M.Kom.', 'Ditawarkan', 1, 0, 0, 4, '4ATI', 'W', '60', 'Teknik Informatika'),
    ('FST6091110', 'Sistem Operasi', 3, 'Jumat', '08.00 - 10.30 WIB', 'Ruang Kelas 3.01 FST', 35, None, 'Victor Amrizal, M.Kom.', 'Ditawarkan', 1, 0, 0, 4, '4BTI', 'W', '60', 'Teknik Informatika'),
    ('FST6091111', 'Teori Bahasa dan Otomata', 3, 'Senin', '13.00 - 15.30 WIB', 'Ruang Kelas 3.03 FST', 35, None, 'Fitri Mintarsih, M.Kom.', 'Ditawarkan', 1, 0, 0, 4, '4CTI', 'W', '60', 'Teknik Informatika'),
    ('FST6091112', 'Analisis dan Desain Algoritma', 3, 'Selasa', '13.00 - 15.30 WIB', 'Ruang Kelas 3.04 FST', 35, None, 'Dr.Imam Marzuki Shofi, M.T.', 'Ditawarkan', 1, 0, 0, 4, '4DTI', 'W', '60', 'Teknik Informatika'),

    # --- SEMESTER 5 (TI) ---
    ('FST6091501', 'Pemrograman Berbasis Platform', 3, 'Rabu', '08.00 - 10.30 WIB', 'Lab Komputer 2 Lt. 3', 35, 'dosen1', 'Luh Kesuma Wardhani, S.T., M.T.', 'Dispensasi Buka', 1, 1, 1, 5, '5ATI', 'W', '60', 'Teknik Informatika'),
    ('FST6091502', 'Keamanan Informasi', 3, 'Kamis', '08.00 - 10.30 WIB', 'Lab Komputer 2 Lt. 3', 35, None, 'Arini, S.T., M.T.', 'Ditawarkan', 1, 0, 0, 5, '5ATI', 'W', '60', 'Teknik Informatika'),
    ('FST6091503', 'Kecerdasan Buatan', 3, 'Senin', '08.00 - 10.30 WIB', 'Ruang Kelas 3.03 FST', 35, None, 'Victor Amrizal, M.Kom.', 'Ditawarkan', 1, 0, 0, 5, '5BTI', 'W', '60', 'Teknik Informatika'),
    ('FST6091504', 'Pemodelan Dan Simulasi', 3, 'Rabu', '08.00 - 10.30 WIB', 'Lab Komputer 1 Lt. 3', 35, None, 'Muhamad Azhari, S.Kom.,M.Kom', 'Ditawarkan', 1, 0, 0, 5, '5ATI', 'W', '60', 'Teknik Informatika'),
    ('FST6091901', 'Penjaminan Mutu Perangkat Lunak (SQA)', 3, 'Jumat', '13.30 - 16.00 WIB', 'Ruang Kelas 3.04 FST', 33, None, 'Rizal, M.Kom.', 'Ditawarkan', 1, 0, 0, 5, '5PTI', 'P', '60', 'Teknik Informatika'),
    ('FST6091903', 'Rekayasa pra-syarat (Requirements Engineering)', 3, 'Selasa', '13.00 - 15.30 WIB', 'Ruang Kelas 3.02 FST', 33, None, 'Dr.Imam Marzuki Shofi, M.T.', 'Ditawarkan', 1, 0, 0, 5, '5PTI', 'P', '60', 'Teknik Informatika'),
    ('FST6091905', 'Rekayasa Perangkat Lunak Lanjut', 3, 'Senin', '10.30 - 13.00 WIB', 'Lab RPL FST Lt. 3', 33, None, 'Rizal, M.Kom.', 'Ditawarkan', 1, 0, 0, 5, '5PTI', 'P', '60', 'Teknik Informatika'),
    ('FST6091907', 'Infrastruktur Teknologi Informasi', 3, 'Rabu', '13.00 - 15.30 WIB', 'Lab Jaringan Lt. 3', 33, None, 'Muhamad Azhari, S.Kom.,M.Kom', 'Ditawarkan', 1, 0, 0, 5, '5PTI', 'P', '60', 'Teknik Informatika'),
    ('FST6091908', 'Arsitektur dan Integrasi Enterprise', 3, 'Jumat', '08.00 - 10.30 WIB', 'Ruang Kelas 3.01 FST', 33, 'prodi', 'Andrew Fiade, M.Kom.', 'Ditawarkan', 1, 0, 0, 5, '5PTI', 'P', '60', 'Teknik Informatika'),
    ('FST6091912', 'Data Science', 3, 'Senin', '13.00 - 15.30 WIB', 'Lab Riset Informatika Lt. 3', 34, 'prodi', 'Siti Ummi Masruroh, M.Sc.', 'Ditawarkan', 1, 0, 0, 5, '5PTI', 'P', '60', 'Teknik Informatika'),
    ('FST6091917', 'Wireless Sensor Network', 3, 'Kamis', '13.00 - 15.30 WIB', 'Lab Jaringan Lt. 3', 33, None, 'Nurhayati, Ph.D.', 'Ditawarkan', 1, 0, 0, 5, '5PTI', 'P', '60', 'Teknik Informatika'),
    ('FST6091918', 'Sistem Benam', 3, 'Rabu', '10.30 - 13.00 WIB', 'Lab Hardware Lt. 2', 33, None, 'Dr.Nenny Anggraini, S.Kom, MT', 'Ditawarkan', 1, 0, 0, 5, '5PTI', 'P', '60', 'Teknik Informatika'),
    ('FST6091926', 'Sistem Basis Data Lanjut', 3, 'Selasa', '10.30 - 13.00 WIB', 'Ruang Teater FST Lt. 2', 30, 'prodi', 'Muhammad Sobri, S.Kom.,M.Kom.,Ph.D', 'Ditawarkan', 1, 0, 0, 5, '5PTI', 'P', '60', 'Teknik Informatika'),
    ('FST6093261', 'Etika Profesi Teknologi Informasi', 2, 'Selasa', '08.00 - 09.40 WIB', 'Ruang Kelas 3.02 FST', 35, None, 'Fenty Eka Muzayyana Agustin, M.Kom.', 'Ditawarkan', 1, 0, 0, 5, '5ATI', 'W', '60', 'Teknik Informatika'),
    ('UIN6000208', 'Metodologi Penelitian', 3, 'Selasa', '10.30 - 13.00 WIB', 'Ruang Kelas 3.01 FST', 35, None, 'Khodijah Hulliyah, M.Si., Ph.D', 'Ditawarkan', 1, 0, 0, 5, '5CTI', 'W', '60', 'Teknik Informatika'),

    # --- SEMESTER 6 (TI) ---
    ('FST6091925', 'Sistem Operasi Lanjut', 3, 'Senin', '13.00 - 15.30 WIB', 'Ruang Kelas 3.01 FST', 33, None, 'Victor Amrizal, M.Kom.', 'Ditawarkan', 1, 0, 0, 6, '6PTI', 'P', '60', 'Teknik Informatika'),
    ('FST6091928', 'Kapita Selekta Komputasi', 3, 'Selasa', '13.00 - 15.30 WIB', 'Ruang Teater FST Lt. 2', 30, None, 'Prof.Husni Teja Sukmana, Ph.D', 'Ditawarkan', 1, 0, 0, 6, '6PTI', 'P', '60', 'Teknik Informatika'),

    # --- PROGRAM STUDI MITRA: SISTEM INFORMASI ('55') untuk Lintas Prodi ---
    ('SIS6091103', 'Basis Data Enterprise (Lintas Prodi)', 3, 'Rabu', '13.00 - 15.30 WIB', 'Lab SI FST Lt. 4', 30, None, 'Arief Fatchul Huda, M.Kom.', 'Ditawarkan', 1, 0, 0, 3, '3ASI', 'W', '55', 'Sistem Informasi'),
    ('SIS6091108', 'Rekayasa Sistem Informasi (Lintas Prodi)', 3, 'Kamis', '10.30 - 13.00 WIB', 'Ruang 4.02 FST', 30, None, 'Zainul Arham, M.Si.', 'Ditawarkan', 1, 0, 0, 3, '3ASI', 'W', '55', 'Sistem Informasi'),
    ('SIS6091502', 'Manajemen Proyek Sistem Informasi', 3, 'Jumat', '13.30 - 16.00 WIB', 'Ruang 4.05 FST', 25, None, 'Nia Kumaladewi, MMSI.', 'Ditawarkan', 1, 0, 0, 5, '5ASI', 'P', '55', 'Sistem Informasi'),

    # --- PROGRAM STUDI ILMU KESEHATAN ('70') untuk Contoh Tarif Rp850.000/SKS ---
    ('KED7091101', 'Anatomi & Histologi Dasar', 3, 'Senin', '08.00 - 10.30 WIB', 'Ruang Kuliah FK 101', 25, None, 'dr. Ahmad Fauzi, M.Kes.', 'Ditawarkan', 1, 0, 0, 1, '1AFK', 'W', '70', 'Pendidikan Dokter'),
]


def _seed_student_grades(conn) -> None:
    """Seed sample course grade history for validating SK Rektor 686/2025 (BR-03)."""
    grade_specs = [
        # IHSAN MUBAROK (IPK 3.75): punya nilai perbaikan C+/C/C-/D/E, nilai lulus A/B, plus banyak MK belum diambil (MK Baru)
        ('1084729301', [
            ('FST6091101', 'C', 1),
            ('FST6091125', 'D', 1),
            ('FST6091201', 'C+', 1),
            ('FST6094102', 'E', 1),
            ('FST6091103', 'C-', 3),
            ('FST6091106', 'D', 3),
            ('FST6091108', 'C', 3),
            ('TIF3101', 'C', 3),
            ('TIF3103', 'D', 3),
            ('UIN6014203', 'A', 3),
            ('NAS6112203', 'B', 1),
        ]),
        # DANUARDI SAPUTRO (IPK 3.65)
        ('1093847152', [
            ('FST6091108', 'C', 3),
            ('FST6091103', 'D', 3),
            ('FST6091101', 'C-', 1),
        ]),
        # MUHAMMAD BAGAS F (IPK 2.85 < 3.00 -> hanya boleh Perbaikan Nilai, tidak boleh MK Baru!)
        ('1072918463', [
            ('FST6091101', 'D', 1),
            ('FST6091125', 'E', 1),
            ('FST6091103', 'C', 3),
            ('FST6091106', 'C-', 3),
            ('FST6091108', 'C', 3),
            ('UIN6014203', 'B', 3),
        ]),
        # REVAND RADITIYA D
        ('1065829174', [
            ('FST6091501', 'C', 5),
            ('FST6091106', 'D', 3),
        ]),
    ]

    for username, grades in grade_specs:
        user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if not user:
            continue
        for course_code, grade, sem_taken in grades:
            conn.execute(
                '''
                INSERT INTO student_grades (student_id, course_code, grade, semester_taken)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (student_id, course_code) DO NOTHING
                ''',
                (user['id'], course_code, grade, sem_taken),
            )


def _seed_announcements_and_proposals(conn) -> None:
    prodi_user = conn.execute("SELECT id FROM users WHERE username = 'prodi'").fetchone()
    creator_id = prodi_user['id'] if prodi_user else None

    if conn.execute("SELECT COUNT(*) AS cnt FROM announcements").fetchone()['cnt'] == 0:
        conn.execute(
            '''
            INSERT INTO announcements (title, content, category, is_active, created_by)
            VALUES (?, ?, ?, 1, ?)
            ''',
            (
                'Jadwal Penyelenggaraan Semester Antara 2026/2027 (SK Rektor 686/2025)',
                (
                    '1) Usulan Mata Kuliah Baru & Lintas Prodi: 20 s.d. 30 Juni 2026. '
                    '2) Pengisian KRS & Verifikasi DPA: 1 s.d. 25 Juli 2026 (Maksimal 9 SKS, Minimal Semester 4). '
                    '3) Penutupan Pendaftaran, Evaluasi Kuota (Min. 10 Mahasiswa/Kelas), & Pembayaran VA: 26 Juli s.d. 5 Agustus 2026.'
                ),
                'Jadwal Resmi',
                creator_id,
            ),
        )
        conn.execute(
            '''
            INSERT INTO announcements (title, content, category, is_active, created_by)
            VALUES (?, ?, ?, 1, ?)
            ''',
            (
                'Ketentuan Kelas Luring & Dispensasi Kuota < 10 Peserta',
                (
                    'Perkuliahan dilaksanakan secara tatap muka luring (16 pertemuan termasuk UTS & UAS). '
                    'Tagihan Virtual Account baru diterbitkan setelah KRS disetujui DPA dan kelas dinyatakan Dibuka oleh Program Studi.'
                ),
                'Aturan Akademik',
                creator_id,
            ),
        )

    if conn.execute("SELECT COUNT(*) AS cnt FROM course_equivalences").fetchone()['cnt'] == 0:
        equivalences = [
            ('EKV-TI-SI-01', 'FST6091103', 'Sistem Basis Data', '60', 'SIS6091103', 'Basis Data Enterprise (Lintas Prodi)', '55', 3, 'Valid'),
            ('EKV-TI-SI-02', 'FST6091108', 'Rekayasa Perangkat Lunak', '60', 'SIS6091108', 'Rekayasa Sistem Informasi (Lintas Prodi)', '55', 3, 'Valid'),
        ]
        conn.executemany(
            '''
            INSERT INTO course_equivalences (
                equivalence_code, kode_mk_asal, nama_mk_asal, prodi_asal_code,
                kode_mk_tujuan, nama_mk_tujuan, prodi_tujuan_code, sks, status_ekuivalen
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (equivalence_code) DO NOTHING
            ''',
            equivalences,
        )

    if conn.execute("SELECT COUNT(*) AS cnt FROM course_proposals").fetchone()['cnt'] == 0:
        bagas = conn.execute("SELECT id FROM users WHERE username = '1072918463'").fetchone()
        danu = conn.execute("SELECT id FROM users WHERE username = '1093847152'").fetchone()
        if bagas:
            conn.execute(
                '''
                INSERT INTO course_proposals (
                    proposal_code, student_id, target_prodi_code, course_code, course_name,
                    sks, semester_target, is_cross_prodi, origin_course_code, origin_course_name,
                    syllabus_summary, reason, status, prodi_asal_status, prodi_tujuan_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (proposal_code) DO NOTHING
                ''',
                (
                    'USL-2026-0001',
                    bagas['id'],
                    '60',
                    'FST6091930',
                    'Pembelajaran Mesin Terapan',
                    3,
                    6,
                    0,
                    None,
                    None,
                    'Silabus 16 pertemuan mencakup regresi, klasifikasi, neural network dasar, & evaluasi model.',
                    'Dibutuhkan oleh 6 mahasiswa angkatan 2023 untuk percepatan tugas akhir.',
                    'Menunggu Persetujuan',
                    'Menunggu',
                    'Menunggu',
                ),
            )
        if danu:
            conn.execute(
                '''
                INSERT INTO course_proposals (
                    proposal_code, student_id, target_prodi_code, course_code, course_name,
                    sks, semester_target, is_cross_prodi, origin_course_code, origin_course_name,
                    syllabus_summary, reason, status, prodi_asal_status, prodi_tujuan_status, equivalence_note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (proposal_code) DO NOTHING
                ''',
                (
                    'USL-2026-0002',
                    danu['id'],
                    '55',
                    'SIS6091505',
                    'Audit & Tata Kelola TI',
                    3,
                    5,
                    1,
                    'FST6091907',
                    'Infrastruktur Teknologi Informasi',
                    'COBIT 2019, manajemen risiko TI, dan tata kelola sistem informasi enterprise.',
                    'Permohonan kelas lintas Prodi Sistem Informasi dengan kesetaraan 3 SKS.',
                    'Menunggu Persetujuan',
                    'Setuju',
                    'Menunggu',
                    'Ekuivalen 3 SKS untuk peminatan manajemen layanan TI.',
                ),
            )


def _seed_demo_applications(conn) -> None:
    """Seed realistic KRS data covering:
    1) Pending DPA application (DANUARDI - Diajukan)
    2) Finalized Lunas / Terdaftar Resmi application (REVAND on FST6091501 Dispensasi Buka)
    3) 10 DPA-approved students enrolled in FST6091108 (RPL) & FST6091103 (SBD) so Prodi can demo >= 10 quota class opening & automatic VA issuance (BR-08)!
    """
    dpa_user = conn.execute("SELECT id FROM users WHERE username = 'dpa1'").fetchone()
    dpa_id = dpa_user['id'] if dpa_user else None

    danu = conn.execute("SELECT id FROM users WHERE username = '1093847152'").fetchone()
    revand = conn.execute("SELECT id FROM users WHERE username = '1065829174'").fetchone()
    c_rpl = conn.execute("SELECT id, sks FROM courses WHERE code = 'FST6091108'").fetchone()
    c_sbd = conn.execute("SELECT id, sks FROM courses WHERE code = 'FST6091103'").fetchone()
    c_pbp = conn.execute("SELECT id, sks FROM courses WHERE code = 'FST6091501'").fetchone()

    # 1. DANUARDI: menunggu verifikasi DPA
    if danu and c_rpl and c_sbd:
        total = c_rpl['sks'] + c_sbd['sks']
        app_id = conn.insert_returning_id(
            '''
            INSERT INTO krs_applications (
                student_id, semester_period, total_sks, status, status_final, preferred_bank
            )
            VALUES (?, 'Semester Antara 2026/2027', ?, 'Diajukan', 'Diajukan', 'BSI')
            ''',
            (danu['id'], total),
        )
        conn.execute(
            '''
            INSERT INTO krs_items (application_id, course_id, status, jenis_pengambilan, nilai_lama)
            VALUES (?, ?, 'Aktif', 'Perbaikan Nilai', 'C')
            ''',
            (app_id, c_rpl['id']),
        )
        conn.execute(
            '''
            INSERT INTO krs_items (application_id, course_id, status, jenis_pengambilan, nilai_lama)
            VALUES (?, ?, 'Aktif', 'Perbaikan Nilai', 'D')
            ''',
            (app_id, c_sbd['id']),
        )

    # 2. REVAND: sudah Disetujui DPA, kelas FST6091501 Dispensasi Buka, & pembayaran Lunas (untuk FR-12 Dosen Pengampu)
    if revand and c_pbp:
        total = c_pbp['sks']
        app_id = conn.insert_returning_id(
            '''
            INSERT INTO krs_applications (
                student_id, semester_period, total_sks, status, status_final,
                dpa_notes, dpa_verified_by, preferred_bank, verified_at
            )
            VALUES (
                ?, 'Semester Antara 2026/2027', ?, 'Lunas', 'Terdaftar Resmi',
                'Disetujui DPA untuk perbaikan nilai mata kuliah wajib.', ?, 'Bank Mandiri', CURRENT_TIMESTAMP
            )
            ''',
            (revand['id'], total, dpa_id),
        )
        conn.execute(
            '''
            INSERT INTO krs_items (application_id, course_id, status, jenis_pengambilan, nilai_lama)
            VALUES (?, ?, 'Aktif', 'Perbaikan Nilai', 'C')
            ''',
            (app_id, c_pbp['id']),
        )
        conn.execute(
            '''
            INSERT INTO invoices (
                application_id, student_id, va_number, bank_name, amount, status,
                expires_at, paid_at, payment_channel, reconciliation_notes
            )
            VALUES (
                ?, ?, '88718291748205', 'Bank Mandiri', ?, 'Lunas',
                '2026-08-05 23:59:59', CURRENT_TIMESTAMP,
                'Rekonsiliasi Manual Bank', 'Ref: ATM-PAY-DEMO-01 | Pembayaran Demo Awal'
            )
            ON CONFLICT (application_id) DO NOTHING
            ''',
            (app_id, revand['id'], total * 220000),
        )

    # 3. 10 Mahasiswa tambahan berstatus Disetujui DPA (Menunggu Kepastian Kelas Buka) pada FST6091108 & FST6091103
    if c_rpl and c_sbd:
        banks = ['Bank Mandiri', 'BNI', 'BRI', 'BTN', 'BSI']
        for idx in range(1, 11):
            uname = f'10519000{idx:02d}'
            stu = conn.execute("SELECT id FROM users WHERE username = ?", (uname,)).fetchone()
            if not stu:
                continue
            total = c_rpl['sks'] + c_sbd['sks']
            app_id = conn.insert_returning_id(
                '''
                INSERT INTO krs_applications (
                    student_id, semester_period, total_sks, status, status_final,
                    dpa_notes, dpa_verified_by, preferred_bank, verified_at
                )
                VALUES (
                    ?, 'Semester Antara 2026/2027', ?, 'Disetujui DPA', 'Menunggu Kepastian Kelas Buka',
                    'Disetujui DPA. Menunggu penetapan pembukaan kelas oleh Prodi.', ?, ?, CURRENT_TIMESTAMP
                )
                ''',
                (stu['id'], total, dpa_id, banks[(idx - 1) % len(banks)]),
            )
            conn.execute(
                '''
                INSERT INTO krs_items (application_id, course_id, status, jenis_pengambilan, nilai_lama)
                VALUES (?, ?, 'Aktif', 'Mata Kuliah Baru', NULL)
                ''',
                (app_id, c_rpl['id']),
            )
            conn.execute(
                '''
                INSERT INTO krs_items (application_id, course_id, status, jenis_pengambilan, nilai_lama)
                VALUES (?, ?, 'Aktif', 'Mata Kuliah Baru', NULL)
                ''',
                (app_id, c_sbd['id']),
            )


LEGACY_STUDENT_NAME_TO_NIM = {
    'IHSAN MUBAROK': '1084729301',
    'DANUARDI SAPUTRO': '1093847152',
    'MUHAMMAD BAGAS F': '1072918463',
    'REVAND RADITIYA D': '1065829174',
}


def _ensure_rbac_demo_accounts(conn) -> None:
    """Ensure all 6 RBAC demo accounts and simulation students exist cleanly even on migrated DBs."""
    # Upgrade very old sample NIM format
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

    # Migrate legacy 'kaprodi' -> 'prodi' if 'prodi' does not yet exist
    legacy_kaprodi = conn.execute("SELECT id FROM users WHERE username = 'kaprodi'").fetchone()
    existing_prodi = conn.execute("SELECT id FROM users WHERE username = 'prodi'").fetchone()
    if legacy_kaprodi and not existing_prodi:
        conn.execute(
            """
            UPDATE users
            SET username = 'prodi', email = 'prodi@uinjkt.ac.id', role = 'prodi',
                password = ?, prodi_code = '60'
            WHERE id = ?
            """,
            (generate_password_hash('prodi123'), legacy_kaprodi['id']),
        )

    # Migrate legacy 'admin_tu' -> 'keuangan' if 'keuangan' does not yet exist
    legacy_admin_tu = conn.execute("SELECT id FROM users WHERE username = 'admin_tu'").fetchone()
    existing_keu = conn.execute("SELECT id FROM users WHERE username = 'keuangan'").fetchone()
    if legacy_admin_tu and not existing_keu:
        conn.execute(
            """
            UPDATE users
            SET username = 'keuangan', email = 'keuangan@uinjkt.ac.id', role = 'keuangan',
                name = 'Biro Perencanaan & Keuangan UIN', nim_nip = 'KEUANGAN-BPK-01',
                prodi = 'Biro Perencanaan & Keuangan', password = ?, prodi_code = '60'
            WHERE id = ?
            """,
            (generate_password_hash('keuangan123'), legacy_admin_tu['id']),
        )

    for (
        username, raw_pw, name, nim_nip, role, prodi, prodi_code,
        ipk, sem, status_sanksi, avatar, email, is_active,
    ) in SEED_USERS:
        existing = conn.execute(
            "SELECT id, password, email, role, prodi_code, status_sanksi FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not existing:
            conn.execute(
                '''
                INSERT INTO users (
                    username, password, name, nim_nip, role, prodi, prodi_code,
                    ipk, semester, status_sanksi, dpa_id, avatar, email, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
                ON CONFLICT (username) DO NOTHING
                ''',
                (
                    username,
                    generate_password_hash(raw_pw),
                    name,
                    nim_nip,
                    role,
                    prodi,
                    prodi_code,
                    ipk,
                    sem,
                    status_sanksi,
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
            if not existing['prodi_code']:
                updates.append("prodi_code = ?")
                params.append(prodi_code)
            if not existing['status_sanksi']:
                updates.append("status_sanksi = ?")
                params.append(status_sanksi)
            if existing['password'] == '123456':
                updates.append("password = ?")
                params.append(generate_password_hash(raw_pw))
            if updates:
                params.append(existing['id'])
                conn.execute(
                    f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                    tuple(params),
                )

    # Normalize deprecated role identifiers on older records
    conn.execute("UPDATE users SET role = 'prodi' WHERE role IN ('kaprodi', 'admin_prodi')")
    conn.execute("UPDATE users SET role = 'keuangan' WHERE role IN ('admin_akademik', 'admin_tu')")

    # Assign dedicated DPA ('dpa1') to students lacking DPA or previously pointing to prodi/kaprodi
    dpa_row = conn.execute("SELECT id FROM users WHERE username = 'dpa1'").fetchone()
    prodi_row = conn.execute("SELECT id FROM users WHERE username = 'prodi'").fetchone()
    if dpa_row:
        if prodi_row:
            conn.execute(
                "UPDATE users SET dpa_id = ? WHERE role = 'mahasiswa' AND (dpa_id IS NULL OR dpa_id = ?)",
                (dpa_row['id'], prodi_row['id']),
            )
        else:
            conn.execute(
                "UPDATE users SET dpa_id = ? WHERE role = 'mahasiswa' AND dpa_id IS NULL",
                (dpa_row['id'],),
            )


def seed_initial_data(conn) -> None:
    for key, value in DEFAULT_CONFIGS:
        conn.execute(
            "INSERT INTO system_config (key, value) VALUES (?, ?) ON CONFLICT (key) DO NOTHING",
            (key, value),
        )

    conn.executemany(
        '''
        INSERT INTO programs (code, name, faculty, rumpun_ilmu, status_buka_sa)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (code) DO NOTHING
        ''',
        SEED_PROGRAMS,
    )

    users_count = conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()['cnt']
    is_fresh_users = users_count == 0
    _ensure_rbac_demo_accounts(conn)

    # Always ensure seeded courses exist (without overwriting existing customizations)
    user_id_by_username = {
        row['username']: row['id']
        for row in conn.execute(
            "SELECT id, username FROM users WHERE username IN ('prodi', 'dosen1', 'dpa1')"
        ).fetchall()
    }
    resolved_courses = [
        (
            code, name, sks, day, time_str, room, quota, 10,
            user_id_by_username.get(lecturer_ref) if lecturer_ref else None,
            lecturer_name, prodi_code, prodi_name, status, agreed, disp_agreed, disp_req,
            1, semester, class_name, wp_type,
        )
        for (
            code, name, sks, day, time_str, room, quota,
            lecturer_ref, lecturer_name, status, agreed, disp_agreed, disp_req,
            semester, class_name, wp_type, prodi_code, prodi_name,
        ) in SEED_COURSES
    ]
    conn.executemany(
        '''
        INSERT INTO courses (
            code, name, sks, schedule_day, schedule_time, room, quota, min_quota,
            lecturer_id, lecturer_name, prodi_code, prodi_name, status, lecturer_agreed,
            lecturer_dispensation_agreed, dispensation_requested, allow_cross_prodi,
            semester, class_name, wp_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (code) DO NOTHING
        ''',
        resolved_courses,
    )

    # Ensure existing courses migrated from old schema have prodi_code populated
    conn.execute("UPDATE courses SET prodi_code = '60' WHERE prodi_code IS NULL OR prodi_code = ''")
    conn.execute("UPDATE courses SET prodi_name = 'Teknik Informatika' WHERE prodi_name IS NULL OR prodi_name = ''")

    _seed_student_grades(conn)
    _seed_announcements_and_proposals(conn)

    apps_count = conn.execute("SELECT COUNT(*) AS cnt FROM krs_applications").fetchone()['cnt']
    if is_fresh_users and apps_count == 0:
        _seed_demo_applications(conn)
