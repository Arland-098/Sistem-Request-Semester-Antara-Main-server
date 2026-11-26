# Sistem Pengajuan Semester Antara Terpusat
**Universitas Islam Negeri Syarif Hidayatullah Jakarta**  
Berdasarkan Keputusan Rektor Nomor 686 Tahun 2025 | Terintegrasi dengan Desain Portal Akademik e-Semesta

---

## 🚀 Panduan Menjalankan Aplikasi

1. **Jalankan Aplikasi:**
   Klik dua kali file `run.bat` atau jalankan perintah berikut di terminal:
   ```powershell
   .\.venv\Scripts\python.exe app.py
   ```
2. **Buka di Peramban Web (Browser):**
   Buka alamat: [http://127.0.0.1:5000](http://127.0.0.1:5000)

3. **Fitur Pengujian Peran (Quick Role Switcher):**
   Di bagian kanan atas bilah navigasi, terdapat tombol dropdown **"Ganti Peran Akses"** untuk beralih antar aktor pengujian:
   - **Mahasiswa** (`Ihsan Mubarok` / 1251420125)
   - **Dosen Pembimbing Akademik** (`Dr. Dewi Khairani, M.Sc.`)
   - **Dosen Pengampu Mata Kuliah** (`Luh Kesuma Wardhani, S.T., M.T.`)
   - **Program Studi** (`Admin Prodi Teknik Informatika`)
   - **Bagian Keuangan** (`Biro Perencanaan dan Keuangan`)

---

## 📋 Matriks Pemenuhan Kebutuhan Fungsional & Non-Fungsional

| Kode | Aktor | Kebutuhan & Implementasi Sistem | Status |
| :--- | :--- | :--- | :---: |
| **FR-03** | Mahasiswa | **Katalog Resmi Mata Kuliah Dibuka:** Menampilkan kode MK, nama mata kuliah, bobot SKS, jadwal sesi perkuliahan, alokasi ruang kelas luring, kapasitas kuota pendaftar, dan dosen pengampu. | ✅ Terpenuhi |
| **FR-04** | Mahasiswa | **Pengisian Kartu Rencana Studi (KRS):** Validasi otomatis beban studi maksimal 9 SKS (SK Rektor 686/2025), pemeriksaan bentrok sesi jadwal luring, dan pencegahan over-quota. | ✅ Terpenuhi |
| **FR-07** | Mahasiswa | **Rincian Tagihan VA & Cetak KRS Sah:** Menampilkan rincian Virtual Account perbankan mitra (Mandiri, BSI, BNI, BRI) dan fitur pencetakan Kartu Rencana Studi Sah berstempel dan QR Code setelah pembayaran lunas. | ✅ Terpenuhi |
| **FR-08** | Dosen PA | **Dasbor Pengajuan Bimbingan:** Menampilkan daftar pengajuan rencana studi mahasiswa bimbingan lengkap dengan riwayat akademik (IPK, SKS, semester). | ✅ Terpenuhi |
| **FR-09** | Dosen PA | **Verifikasi Persetujuan DPA:** Opsi persetujuan (*Setujui* atau *Tolak* disertai input catatan/arahan perbaikan bagi mahasiswa). | ✅ Terpenuhi |
| **FR-10** | Dosen Pengampu | **Konfirmasi Kesediaan Mengajar:** Fitur bagi calon dosen pengampu untuk mengonfirmasi kesediaan mengajar mata kuliah pada masa jeda semester. | ✅ Terpenuhi |
| **FR-11** | Dosen Pengampu | **Konfirmasi Kelas Dispensasi:** Fitur konfirmasi kesediaan mengajar kelas dispensasi apabila pendaftar berjumlah di bawah 10 peserta. | ✅ Terpenuhi |
| **FR-14** | Program Studi | **Pengaturan Periode & Status Keaktifan:** Mengatur status periode pendaftaran (*Buka* / *Tutup*), rentang tanggal, dan batas beban studi. | ✅ Terpenuhi |
| **FR-17** | Program Studi | **Pengelolaan Katalog MK & Kuota:** Tambah mata kuliah baru, ubah kapasitas kuota kelas, serta penugasan dosen pengampu. | ✅ Terpenuhi |
| **FR-18** | Program Studi | **Jadwal Kuliah Luring & Alokasi Ruang:** Mengatur jadwal hari, jam sesi tatap muka intensif, dan alokasi ruang kelas / laboratorium di FST. | ✅ Terpenuhi |
| **FR-19** | Program Studi | **Monitoring Kuota & Status Kelas:** Memantau kuota secara real-time dan menetapkan status kelas (*Dibuka*, *Dispensasi Buka*, atau *Dibatalkan*). | ✅ Terpenuhi |
| **FR-20** | Program Studi | **Penutupan Pendaftaran & Ekspor Peserta:** Mengunci pendaftaran resmi dan mengekspor rekapitulasi peserta resmi ke file CSV / Excel. | ✅ Terpenuhi |
| **FR-21** | Bagian Keuangan | **Pengaturan Tarif Biaya per SKS:** Mengatur parameter biaya per SKS sesuai Keputusan Rektor No. 686 Tahun 2025 (default Rp220.000 / SKS). | ✅ Terpenuhi |
| **FR-22** | Bagian Keuangan | **Penerbitan Nomor Virtual Account Otomatis:** Sistem menerbitkan nomor VA 16-digit mitra bank dan faktur tagihan otomatis saat pengajuan disetujui DPA. | ✅ Terpenuhi |
| **FR-23** | Bagian Keuangan | **Pemantauan Pembayaran & Rekonsiliasi Manual:** Memantau status pembayaran dan melakukan rekonsiliasi manual dengan nomor referensi transfer bank. | ✅ Terpenuhi |
| **NFR-03** | Sistem / Data | **Keandalan Data (Data Reliability & Synchronization):** Menerapkan mekanisme transaksi atomik database (`isolation_level = EXCLUSIVE`) dan pengecekan kapasitas kuota saat pendaftaran agar jumlah pendaftar tidak melampaui kuota kelas. | ✅ Terpenuhi |

---

## 🎨 Keselarasan Desain dengan Portal Akademik
Website dirancang selaras dengan antarmuka **[Portal Akademik.html](Portal%20Akademik.html)** UIN Syarif Hidayatullah Jakarta:
- Menggunakan palet warna resmi hijau tua UIN (`#004d26`) dan aksen emas (`#d4af37`).
- Memanfaatkan seluruh aset font, stylesheet (`gsStyle_main_eCampuz_v2.0.css`, `gsStyle_content_eCampuz_v2.0.css`), logo universitas, ikon FontAwesome, dan komponen tabel Bootstrap.
- Struktur tata letak e-Semesta lengkap dengan header universitas, user badge avatar, breadcrumb navigasi, alert info/warning, hingga format kop surat resmi untuk cetak dokumen KRS.
