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

## 🔐 Autentikasi & 6 Akun Demo (Sesuai Dokumen PDF + Super Admin)

Seluruh halaman utama dilindungi oleh autentikasi berbasis Flask `session` (menggunakan `SECRET_KEY` dari `.env` / Environment Variables). Di halaman `/login`, tersedia kotak info berisi 6 akun demo (5 Aktor Resmi Dokumen Spesifikasi + Super Admin):

| Peran | Username | Email | Password | Hak Akses |
| :--- | :--- | :--- | :--- | :--- |
| **Mahasiswa** | `1084729301` | `mahasiswa@uinjkt.ac.id` | `mhs123` | Lihat pengumuman & katalog Prodi/lintas Prodi, usul MK baru, isi/ubah KRS, pantau VA & cetak KRS sah |
| **Dosen PA (DPA)** | `dpa1` | `dpa@uinjkt.ac.id` | `dpa123` | Memeriksa riwayat IPK/SKS/sanksi mahasiswa bimbingan & menyetujui/menolak KRS (UC-DPA-02) |
| **Dosen Pengampu** | `dosen1` | `dosen@uinjkt.ac.id` | `dosen123` | Konfirmasi kesediaan mengajar (FR-10), kelas dispensasi `<10` (FR-11), & daftar peserta lunas (FR-12) |
| **Program Studi** | `prodi` | `prodi@uinjkt.ac.id` | `prodi123` | Kelola pengumuman, periode, usulan MK & ekuivalensi, katalog MK, jadwal/ruang, evaluasi kuota & rekap CSV |
| **Bagian Keuangan** | `keuangan` | `keuangan@uinjkt.ac.id` | `keuangan123` | Atur tarif SKS (Non-Kesehatan/Kesehatan), terbitkan/pantau tagihan VA kelas buka, rekonsiliasi & cek Expired |
| **Super Admin** | `superadmin` | `superadmin@uinjkt.ac.id` | `superadmin123` | Akses penuh seluruh sistem, manajemen pengguna (`/admin/users`), master mahasiswa/nilai, dosen, & prodi |

---

## 📋 Matriks Pemenuhan Kebutuhan Fungsional & Bisnis (Dokumen PDF)

| Kode | Aktor | Kebutuhan & Implementasi Sistem | Status |
| :--- | :--- | :--- | :---: |
| **FR-01 & FR-13** | Program Studi & Mahasiswa | **Pengumuman Resmi SA:** Prodi mempublikasikan pengumuman & jadwal yang langsung tampil di Beranda Mahasiswa. | ✅ Terpenuhi |
| **FR-02, FR-15, FR-16** | Mahasiswa & Prodi | **Usulan MK Baru & Lintas Prodi (AD-01):** Pengajuan usulan MK internal maupun lintas Prodi disertai silabus & tabel ekuivalensi `EKUIVALENSI_MK`. | ✅ Terpenuhi |
| **FR-03** | Mahasiswa | **Katalog Resmi Mata Kuliah:** Kode, nama, SKS, jadwal sesi, ruang luring, kuota, dosen pengampu, & filter Program Studi. | ✅ Terpenuhi |
| **FR-04, FR-05, FR-06** | Mahasiswa | **Pengisian, Revisi & Pembatalan KRS (BR-03):** Validasi otomatis Semester &ge; 4, Bebas Sanksi, Maks 9 SKS, Perbaikan Nilai (`C+`..`E`), MK Baru (`IPK >= 3.00`), anti-bentrok, ubah & batalkan sebelum tutup. | ✅ Terpenuhi |
| **FR-07** | Mahasiswa | **Rincian Tagihan VA & Cetak KRS Sah:** Rincian Virtual Account bank mitra dan cetak KRS sah berstempel DPA & QR Code setelah lunas. | ✅ Terpenuhi |
| **FR-08 & FR-09** | Dosen PA (DPA) | **Dasbor Verifikasi Bimbingan DPA:** Daftar KRS khusus mahasiswa bimbingan (`dpa_id`), memeriksa IPK/semester/sanksi/MK, Setuju atau Tolak (tanpa menerbitkan VA prematur). | ✅ Terpenuhi |
| **FR-10, FR-11, FR-12** | Dosen Pengampu | **Konfirmasi Mengajar, Dispensasi & Peserta Lunas:** Konfirmasi kesediaan mengajar, respon dispensasi `< 10` (SD-03), dan daftar peserta resmi Lunas. | ✅ Terpenuhi |
| **FR-14, FR-17–FR-20** | Program Studi | **Periode, Katalog, Jadwal/Ruang, Evaluasi Kuota & Ekspor CSV:** Penetapan kelas `Dibuka`/`Dispensasi Buka`/`Dibatalkan` terkunci sebelum penutupan (`UC-PRD-07`) + `BR-07`. | ✅ Terpenuhi |
| **FR-21, FR-22, FR-23** | Bagian Keuangan | **Tarif Dual Rumpun (`Rp220rb` & `Rp850rb`), Penerbitan VA (`BR-08`), Rekonsiliasi & Expired (`Auto-Check 5`):** Mendukung 5 bank mitra (`Mandiri`, `BNI`, `BRI`, `BTN`, `BSI`). | ✅ Terpenuhi |
| **NFR-03** | Sistem / Data | **Keandalan Data:** Transaksi atomik database (`BEGIN EXCLUSIVE` / `FOR UPDATE`) & pencegahan over-quota kelas. | ✅ Terpenuhi |