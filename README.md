# Sistem Pengajuan Semester Antara Terpusat

**Universitas Islam Negeri Syarif Hidayatullah Jakarta**  
Berdasarkan Keputusan Rektor Nomor 686 Tahun 2025 | Terintegrasi dengan Desain Portal Akademik e-Semesta

---

## 📁 Struktur Proyek

Struktur proyek telah dirapikan secara modular agar mudah di-deploy ke hosting maupun dikembangkan untuk fitur tambahan:

```text
.
├── app.py                  # Entry point utama & Flask application factory (create_app)
├── config.py               # Konfigurasi terpusat (.env, DATABASE_URL PostgreSQL, & fallback SQLite)
├── wsgi.py                 # Entry point WSGI untuk server produksi (Gunicorn / PythonAnywhere)
├── vercel.json             # Konfigurasi Vercel Serverless Functions
├── .vercelignore           # Pengecualian file non-runtime saat deploy ke Vercel
├── Procfile                # Konfigurasi start command untuk PaaS (Render, Railway, Heroku)
├── Dockerfile              # Konfigurasi container untuk Docker / Fly.io / VPS
├── requirements.txt        # Daftar dependensi Python (Flask, gunicorn, psycopg[binary], python-dotenv)
├── .env.example            # Template variabel environment
├── run.bat                 # Launcher cepat untuk Windows lokal
│
├── database/
│   ├── connection.py       # Dual-backend adapter (PostgreSQL cloud via DATABASE_URL & SQLite lokal)
│   └── seed.py             # Data awal lengkap (konfigurasi, akun demo, & 45 mata kuliah)
│
├── services/               # Layer logika bisnis & query database per domain
│   ├── config_service.py   # Pengaturan periode, tarif SKS, batas SKS
│   ├── user_service.py     # Manajemen lookup akun & dosen
│   ├── course_service.py   # Katalog MK, jadwal, ruang, kuota, konfirmasi dosen
│   ├── krs_service.py      # Pengajuan KRS atomik (NFR-03), validasi SKS/jadwal, verifikasi DPA
│   └── billing_service.py  # Tagihan Virtual Account, rekonsiliasi manual, & rekap peserta
│
├── routes/                 # Flask Blueprints per aktor / modul
│   ├── main.py             # Beranda (/), health check (/health), switch role
│   ├── mahasiswa.py        # /katalog, /krs, /tagihan, /cetak_krs
│   ├── dpa.py              # /dpa, /dpa/approve, /dpa/reject
│   ├── dosen.py            # /dosen, /dosen/confirm, /dosen/dispensasi
│   ├── prodi.py            # /prodi/periode, /prodi/katalog, /prodi/jadwal_ruang, /prodi/monitoring, /prodi/rekap
│   └── keuangan.py         # /keuangan/tarif, /keuangan/pembayaran, /keuangan/rekonsiliasi
│
├── public/
│   └── static/             # Aset statis (dilayani CDN di Vercel & /static di Flask lokal)
│       ├── css/            # Stylesheet Bootstrap, e-Semesta, & app.css
│       ├── js/             # jQuery & Bootstrap JS
│       └── img/            # Logo universitas & avatar default
│
├── templates/              # Template HTML Jinja2
├── tests/                  # Automated test suite (unittest)
└── docs/                   # Dokumen spesifikasi RPL & referensi tampilan Portal Akademik
```

---

## 🚀 Menjalankan Secara Lokal

### 1. Buat Virtual Environment & Install Dependensi

**Windows (PowerShell / CMD):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Jalankan Server Lokal

- **Windows:** klik dua kali `run.bat` atau jalankan:
  ```powershell
  python app.py
  ```
- **Linux / macOS:**
  ```bash
  FLASK_DEBUG=1 python app.py
  ```

Buka peramban web ke: [http://127.0.0.1:5000](http://127.0.0.1:5000)

Jika `DATABASE_URL` belum diisi, database SQLite lokal (`instance/academic.db`) akan dibuat dan diisi otomatis (`45` mata kuliah, `8` akun demo, serta pengaturan awal) saat aplikasi dijalankan pertama kali.

---

## 🌐 Panduan Push & Deploy ke Hosting

### Opsi 1: Vercel + Cloud PostgreSQL (Direkomendasikan untuk Serverless)
1. Siapkan database PostgreSQL cloud gratis (misalnya **Neon**, **Supabase**, atau **Vercel Postgres** di tab Storage Vercel) dan salin connection string-nya (`postgresql://...`).
2. Import repository GitHub ini di dashboard **Vercel**.
3. Di menu **Settings → Environment Variables** di Vercel, tambahkan:
   - `SECRET_KEY` = string acak panjang yang aman
   - `DATABASE_URL` = connection string PostgreSQL Anda *(jika menggunakan integrasi Vercel Postgres / Neon yang otomatis mengisi `POSTGRES_URL`, aplikasi juga langsung mengenalinya)*
4. Klik **Deploy**. Vercel akan membaca `app.py`, `requirements.txt`, `vercel.json`, dan melayani aset `public/static/` melalui CDN. Tabel serta 45 mata kuliah awal akan otomatis dibuat pada request pertama.

*(Catatan: apabila `DATABASE_URL` belum diisi di Vercel, aplikasi otomatis menggunakan fallback sementara `/tmp/academic.db` agar tidak terkena error read-only filesystem `/var/task`, namun data hanya bersifat sementara per-instance sampai `DATABASE_URL` PostgreSQL diset.)*

### Opsi 2: Render / Railway
1. Hubungkan repository GitHub ini ke layanan **Render** (Web Service) atau **Railway**.
2. Gunakan konfigurasi dari `Procfile` & `requirements.txt`:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
3. Tambahkan **Environment Variables**:
   - `SECRET_KEY` = string acak yang aman
   - `DATABASE_URL` = connection string PostgreSQL **atau** `DATABASE_PATH=/var/data/academic.db` jika memakai Persistent Disk SQLite.
4. Endpoint health check tersedia di `/health`.

### Opsi 3: PythonAnywhere
1. Clone repository ini di PythonAnywhere dan buat virtualenv dengan `pip install -r requirements.txt`.
2. Pada file konfigurasi **WSGI**, arahkan ke `wsgi.py`:
   ```python
   import sys
   sys.path.insert(0, '/home/<username>/Sistem-Request-Semester-Antara-Main-server')
   from wsgi import application
   ```
3. Atur static mapping URL `/static/` ke folder `<project_dir>/public/static`.

### Opsi 4: Docker / VPS
```bash
docker build -t semester-antara .
docker run -d -p 5000:5000 -e SECRET_KEY="ganti-rahasia" -v semesta_data:/app/instance semester-antara
```

---

## 🛠️ Panduan Menambah Fitur Tambahan

Karena kode sudah dipisahkan berdasarkan peran dan tanggung jawab, menambah fitur baru sangat mudah:

1. **Tambah logika database / bisnis** di folder `services/` (misal buat `services/notifikasi_service.py` atau tambah fungsi di service terkait).
2. **Tambah endpoint / halaman baru** di folder `routes/`:
   - Untuk fitur aktor yang sudah ada (misal Mahasiswa), cukup tambahkan `@mahasiswa_bp.route(...)` di `routes/mahasiswa.py`.
   - Untuk modul baru, buat blueprint baru di `routes/` lalu daftarkan di `routes/__init__.py`.
3. **Tambah tampilan HTML** di folder `templates/` dengan mewarisi `{% extends 'base.html' %}` dan menambahkan CSS/JS kustom di `static/css/` atau `static/js/`.
4. **Tambah pengujian** di `tests/test_app.py` lalu jalankan:
   ```bash
   python -m unittest discover -s tests -v
   ```

---

## 🔐 Autentikasi & 5 Akun Demo (RBAC)

Seluruh halaman utama dilindungi oleh autentikasi berbasis Flask `session` (menggunakan `SECRET_KEY` dari `.env` / Environment Variables). Di halaman `/login`, tersedia kotak info berisi 5 akun demo siap pakai:

| Peran | Username | Email | Password | Hak Akses |
| :--- | :--- | :--- | :--- | :--- |
| **Mahasiswa** | `1251420125` | `mahasiswa@uinjkt.ac.id` | `mhs123` | Mengajukan KRS semester antara & melihat status pengajuan sendiri |
| **Dosen Pengampu** | `dosen1` | `dosen@uinjkt.ac.id` | `dosen123` | Melihat MK & pengajuan terkait serta memberi persetujuan/catatan akademik |
| **Kaprodi / Koordinator** | `kaprodi` | `kaprodi@uinjkt.ac.id` | `kaprodi123` | Memverifikasi seluruh pengajuan, mengelola jadwal/kelas, & melihat rekap |
| **Admin Akademik / TU** | `admin_tu` | `admin.tu@uinjkt.ac.id` | `admin123` | Mengelola data master (mahasiswa, dosen, MK) & memproses administrasi pengajuan |
| **Super Admin** | `superadmin` | `superadmin@uinjkt.ac.id` | `superadmin123` | Akses penuh ke seluruh menu sistem & manajemen pengguna (`/admin/users`) |

---

## 📋 Matriks Pemenuhan Kebutuhan Fungsional & Non-Fungsional

| Kode | Aktor | Kebutuhan & Implementasi Sistem | Status |
| :--- | :--- | :--- | :---: |
| **FR-03** | Mahasiswa | **Katalog Resmi Mata Kuliah Dibuka:** Kode MK, nama, bobot SKS, jadwal sesi, ruang luring, kuota, dan dosen pengampu. | ✅ Terpenuhi |
| **FR-04** | Mahasiswa | **Pengisian KRS:** Validasi otomatis maksimal 9 SKS (SK Rektor 686/2025), anti-bentrok jadwal luring, dan cek kuota. | ✅ Terpenuhi |
| **FR-07** | Mahasiswa | **Rincian Tagihan VA & Cetak KRS Sah:** Rincian Virtual Account bank mitra dan cetak KRS sah berstempel & QR Code setelah lunas. | ✅ Terpenuhi |
| **FR-08** | Dosen PA | **Dasbor Pengajuan Bimbingan:** Daftar pengajuan KRS mahasiswa bimbingan beserta riwayat akademik (IPK, SKS, semester). | ✅ Terpenuhi |
| **FR-09** | Dosen PA | **Verifikasi Persetujuan DPA:** Setujui atau tolak pengajuan disertai catatan arahan perbaikan. | ✅ Terpenuhi |
| **FR-10** | Dosen Pengampu | **Konfirmasi Kesediaan Mengajar:** Konfirmasi kesediaan mengampu mata kuliah pada masa jeda semester. | ✅ Terpenuhi |
| **FR-11** | Dosen Pengampu | **Konfirmasi Kelas Dispensasi:** Konfirmasi kesediaan mengajar kelas dispensasi apabila pendaftar di bawah 10 peserta. | ✅ Terpenuhi |
| **FR-14** | Program Studi | **Pengaturan Periode & Status Keaktifan:** Atur status pendaftaran (*Buka*/*Tutup*), rentang tanggal, dan batas beban studi. | ✅ Terpenuhi |
| **FR-17** | Program Studi | **Pengelolaan Katalog MK & Kuota:** Tambah/edit/hapus mata kuliah, atur kuota kelas, dan tugaskan dosen pengampu. | ✅ Terpenuhi |
| **FR-18** | Program Studi | **Jadwal Kuliah Luring & Alokasi Ruang:** Atur hari, jam sesi tatap muka, dan ruang kelas/laboratorium FST. | ✅ Terpenuhi |
| **FR-19** | Program Studi | **Monitoring Kuota & Status Kelas:** Pantau kuota real-time dan tetapkan status kelas (*Dibuka*, *Dispensasi Buka*, *Dibatalkan*). | ✅ Terpenuhi |
| **FR-20** | Program Studi | **Penutupan Pendaftaran & Ekspor Peserta:** Kunci pendaftaran resmi dan ekspor data peserta resmi ke CSV. | ✅ Terpenuhi |
| **FR-21** | Bagian Keuangan | **Pengaturan Tarif Biaya per SKS:** Atur tarif SKS sesuai SK Rektor No. 686/2025 (default Rp220.000/SKS). | ✅ Terpenuhi |
| **FR-22** | Bagian Keuangan | **Penerbitan Nomor Virtual Account Otomatis:** Terbitkan 16-digit nomor VA dan faktur tagihan otomatis saat KRS disetujui DPA. | ✅ Terpenuhi |
| **FR-23** | Bagian Keuangan | **Pemantauan Pembayaran & Rekonsiliasi Manual:** Pantau status pembayaran dan rekonsiliasi manual dengan nomor referensi bank. | ✅ Terpenuhi |
| **NFR-03** | Sistem / Data | **Keandalan Data:** Transaksi atomik database (`BEGIN EXCLUSIVE`) dan proteksi kuota kelas saat pendaftaran bersamaan. | ✅ Terpenuhi |