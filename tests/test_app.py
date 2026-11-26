import datetime
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from flask import render_template

from app import create_app
from config import _resolve_db_path, normalize_database_url
from database import get_db, init_db, translate_placeholders
from services import get_courses_list, get_user_by_username


class SemesterAntaraAuthAndRbacTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.app = create_app({
            'TESTING': True,
            'DATABASE_URL': None,
            'DATABASE_PATH': self.db_path,
            'SECRET_KEY': 'test-secret-key',
        })
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        for ext in ('', '-wal', '-shm'):
            path = f'{self.db_path}{ext}'
            if os.path.exists(path):
                os.unlink(path)

    def _login(self, identifier: str, password: str):
        return self.client.post(
            '/login',
            data={'identifier': identifier, 'password': password},
            follow_redirects=True,
        )

    def _logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_postgres_helpers_and_vercel_tmp_fallback(self):
        self.assertEqual(
            normalize_database_url('postgres://user:pass@host/db?sslmode=require'),
            'postgresql://user:pass@host/db?sslmode=require',
        )
        self.assertIsNone(normalize_database_url('   '))

        sql = "SELECT * FROM users WHERE username = ? AND note = 'kenapa?'"
        self.assertEqual(
            translate_placeholders(sql),
            "SELECT * FROM users WHERE username = %s AND note = 'kenapa?'",
        )

        with patch.dict(os.environ, {'VERCEL': '1', 'DATABASE_PATH': ''}, clear=False):
            self.assertEqual(_resolve_db_path(), '/tmp/academic.db')

    def test_cetak_krs_handles_postgres_datetime_objects(self):
        with self.app.test_request_context('/cetak_krs'):
            html = render_template(
                'mahasiswa_cetak_krs.html',
                student={'nim_nip': '1084729301', 'name': 'IHSAN', 'prodi': 'TI', 'semester': 6, 'ipk': 3.75, 'dpa_name': 'Dr. Dewi'},
                app={'id': 1, 'total_sks': 3, 'submitted_at': datetime.datetime(2026, 11, 26, 8, 30, 0), 'verified_at': datetime.datetime(2026, 11, 26, 9, 0, 0)},
                items=[],
                invoice={'va_number': '8871729301123456'},
            )
        self.assertIn('Ciputat, 2026-11-26', html)

    def test_compat_connection_postgres_mode_translates_queries_and_returning(self):
        from database.connection import CompatConnection

        mock_raw = MagicMock()
        mock_raw.execute.return_value.fetchone.return_value = {'id': 42}
        conn = CompatConnection(mock_raw, backend='postgres')

        inserted_id = conn.insert_returning_id(
            "INSERT INTO krs_applications (student_id, semester_period, total_sks, status) VALUES (?, ?, ?, 'Diajukan')",
            (1, '2026', 3),
        )
        self.assertEqual(inserted_id, 42)
        called_sql = mock_raw.execute.call_args[0][0]
        self.assertIn('%s', called_sql)
        self.assertIn('RETURNING id', called_sql)

    def test_unauthenticated_protection_and_login_page_demo_box(self):
        # Public endpoints work
        with self.client.get('/health') as res_health:
            self.assertEqual(res_health.status_code, 200)
            self.assertEqual(res_health.get_json(), {'status': 'ok'})

        with self.client.get('/login') as res_login:
            self.assertEqual(res_login.status_code, 200)
            for marker in (
                b'1084729301',
                b'mahasiswa@uinjkt.ac.id',
                b'mhs123',
                b'dosen1',
                b'dosen123',
                b'kaprodi',
                b'kaprodi123',
                b'admin_tu',
                b'admin123',
                b'superadmin',
                b'superadmin123',
            ):
                self.assertIn(marker, res_login.data)

        # Static assets work
        for static_path, mime_fragment in {
            '/static/css/app.css': 'text/css',
            '/static/js/bootstrap.min.js': 'javascript',
            '/static/img/logo_client.png': 'image/png',
        }.items():
            with self.client.get(static_path) as res_static:
                self.assertEqual(res_static.status_code, 200)
                self.assertIn(mime_fragment, res_static.content_type)

        # Protected routes redirect to /login when unauthenticated
        for protected_path in (
            '/',
            '/katalog',
            '/krs',
            '/tagihan',
            '/dosen',
            '/dpa',
            '/prodi/monitoring',
            '/prodi/katalog',
            '/master/mahasiswa',
            '/keuangan/pembayaran',
            '/admin/users',
        ):
            res = self.client.get(protected_path)
            self.assertEqual(res.status_code, 302, f'Expected redirect on {protected_path}')
            self.assertIn('/login', res.headers['Location'])

    def test_login_by_username_or_email_wrong_password_and_logout(self):
        # Wrong password fails
        res_bad = self._login('1084729301', 'salah')
        self.assertIn(b'Username/email atau password salah', res_bad.data)
        res_home = self.client.get('/')
        self.assertEqual(res_home.status_code, 302)

        # Login with email works
        res_email = self._login('kaprodi@uinjkt.ac.id', 'kaprodi123')
        self.assertEqual(res_email.status_code, 200)
        self.assertIn(b'Kaprodi / Koordinator', res_email.data)

        # Logout clears session
        res_out = self._logout()
        self.assertIn(b'berhasil logout', res_out.data)
        self.assertEqual(self.client.get('/').status_code, 302)

        # Open redirect prevented
        res_open = self.client.post(
            '/login',
            data={'identifier': 'dosen@uinjkt.ac.id', 'password': 'dosen123', 'next': '//evil.com'},
        )
        self.assertEqual(res_open.status_code, 302)
        self.assertFalse(res_open.headers['Location'].startswith('//evil.com'))

    def test_rbac_menu_and_direct_url_boundaries_for_all_5_roles(self):
        # 1. Mahasiswa
        self._login('1084729301', 'mhs123')
        home_mhs = self.client.get('/').data
        self.assertIn(b'/krs', home_mhs)
        self.assertNotIn(b'/admin/users', home_mhs)
        self.assertNotIn(b'/master/mahasiswa', home_mhs)
        self.assertEqual(self.client.get('/katalog').status_code, 200)
        self.assertEqual(self.client.get('/krs').status_code, 200)
        for forbidden in ('/dosen', '/dpa', '/prodi/monitoring', '/prodi/katalog', '/master/mahasiswa', '/keuangan/pembayaran', '/admin/users'):
            res = self.client.get(forbidden, follow_redirects=True)
            self.assertIn(b'Akses ditolak', res.data, f'Mahasiswa should be blocked from {forbidden}')
        self._logout()

        # 2. Dosen Pengampu
        self._login('dosen1', 'dosen123')
        home_dosen = self.client.get('/').data
        self.assertIn(b'/dosen', home_dosen)
        self.assertNotIn(b'/prodi/katalog', home_dosen)
        self.assertEqual(self.client.get('/dosen').status_code, 200)
        for forbidden in ('/krs', '/dpa', '/prodi/monitoring', '/prodi/katalog', '/master/mahasiswa', '/admin/users'):
            res = self.client.get(forbidden, follow_redirects=True)
            self.assertIn(b'Akses ditolak', res.data, f'Dosen should be blocked from {forbidden}')
        self._logout()

        # 3. Kaprodi / Koordinator
        self._login('kaprodi', 'kaprodi123')
        for allowed in ('/dpa', '/prodi/periode', '/prodi/jadwal_ruang', '/prodi/monitoring', '/prodi/rekap'):
            self.assertEqual(self.client.get(allowed).status_code, 200)
        for forbidden in ('/krs', '/dosen', '/prodi/katalog', '/master/mahasiswa', '/keuangan/pembayaran', '/admin/users'):
            res = self.client.get(forbidden, follow_redirects=True)
            self.assertIn(b'Akses ditolak', res.data, f'Kaprodi should be blocked from {forbidden}')
        self._logout()

        # 4. Admin Akademik / TU
        self._login('admin_tu', 'admin123')
        for allowed in ('/master/mahasiswa', '/master/dosen', '/prodi/katalog', '/keuangan/pembayaran', '/keuangan/tarif', '/prodi/rekap'):
            self.assertEqual(self.client.get(allowed).status_code, 200)
        for forbidden in ('/krs', '/dosen', '/dpa', '/prodi/periode', '/admin/users'):
            res = self.client.get(forbidden, follow_redirects=True)
            self.assertIn(b'Akses ditolak', res.data, f'Admin TU should be blocked from {forbidden}')
        self._logout()

        # 5. Super Admin
        self._login('superadmin', 'superadmin123')
        for allowed in ('/', '/katalog', '/krs', '/dosen', '/dpa', '/prodi/periode', '/prodi/katalog', '/master/mahasiswa', '/master/dosen', '/keuangan/pembayaran', '/admin/users'):
            self.assertEqual(self.client.get(allowed).status_code, 200, f'Superadmin failed on {allowed}')
        self._logout()

    def test_seeded_catalog_has_all_45_courses(self):
        with self.app.app_context():
            courses = get_courses_list()
        self.assertEqual(len(courses), 45)

    def test_multi_role_end_to_end_krs_dosen_kaprodi_admin_and_cetak(self):
        with self.app.app_context():
            courses = get_courses_list()
            by_code = {c['code']: c for c in courses}
            student = get_user_by_username('1084729301')

        # 1. Mahasiswa logs in, checks validation & submits 6 SKS KRS
        self._login('1084729301', 'mhs123')
        self.assertIn(b'status pembayaran lunas', self.client.get('/cetak_krs', follow_redirects=True).data)

        c1_id = by_code['FST6091101']['id']  # taught by dosen1
        c2_id = by_code['FST6091125']['id']
        res_submit = self.client.post(
            '/krs/submit',
            data={'course_ids': [c1_id, c2_id]},
            follow_redirects=True,
        )
        self.assertIn(b'berhasil diajukan', res_submit.data)

        with self.app.app_context():
            conn = get_db()
            try:
                app_row = conn.execute(
                    "SELECT * FROM krs_applications WHERE student_id = ?",
                    (student['id'],),
                ).fetchone()
            finally:
                conn.close()
        app_id = app_row['id']
        self._logout()

        # 2. Dosen Pengampu logs in, sees Ihsan's submission & gives academic approval + notes
        self._login('dosen1', 'dosen123')
        res_dosen = self.client.get('/dosen')
        self.assertIn(b'IHSAN MUBAROK', res_dosen.data)
        res_review = self.client.post(
            f'/dosen/review/{app_id}',
            data={'decision': 'approve', 'notes': 'Nilai dasar pemrograman memenuhi.'},
            follow_redirects=True,
        )
        self.assertIn(b'Persetujuan akademik', res_review.data)

        # Dosen cannot confirm unrelated course owned by kaprodi
        unrelated_course_id = by_code['TIF3102']['id']
        res_unauth = self.client.post(
            f'/dosen/confirm/{unrelated_course_id}',
            data={'agreed': '1'},
            follow_redirects=True,
        )
        self.assertIn(b'tidak berwenang', res_unauth.data)
        self._logout()

        # 3. Kaprodi logs in, sees lecturer notes & approves -> creates VA invoice
        self._login('kaprodi', 'kaprodi123')
        res_dpa = self.client.get('/dpa')
        self.assertIn(b'Nilai dasar pemrograman memenuhi.', res_dpa.data)
        res_approve = self.client.post(f'/dpa/approve/{app_id}', follow_redirects=True)
        self.assertIn(b'DISETUJUI', res_approve.data)

        with self.app.app_context():
            conn = get_db()
            try:
                inv = conn.execute(
                    "SELECT * FROM invoices WHERE application_id = ?",
                    (app_id,),
                ).fetchone()
            finally:
                conn.close()
        self.assertIsNotNone(inv)

        # Cancel c2 -> SKS & invoice recalculated without deadlock
        self.client.post(f'/prodi/status/{c2_id}', data={'status': 'Dibatalkan'}, follow_redirects=True)
        self._logout()

        # 4. Admin Akademik / TU logs in & reconciles payment
        self._login('admin_tu', 'admin123')
        res_pay = self.client.post(
            f"/keuangan/rekonsiliasi/{inv['id']}",
            data={'ref_no': 'REF-TEST-001', 'notes': 'Lunas test'},
            follow_redirects=True,
        )
        self.assertIn(b'DIREKONSILIASI LUNAS', res_pay.data)
        self._logout()

        # 5. Mahasiswa logs in & prints official KRS
        self._login('1084729301', 'mhs123')
        res_print = self.client.get('/cetak_krs')
        self.assertEqual(res_print.status_code, 200)
        self.assertIn(b'KARTU RENCANA STUDI (KRS) SAH', res_print.data)

    def test_admin_master_and_superadmin_user_management(self):
        # Admin TU creates Mahasiswa, Dosen, and MK
        self._login('admin_tu', 'admin123')
        res_mhs = self.client.post(
            '/master/mahasiswa/add',
            data={'nim_nip': '1099887766', 'name': 'Mahasiswa Uji', 'email': 'uji@uinjkt.ac.id', 'password': 'mhs123'},
            follow_redirects=True,
        )
        self.assertIn(b'berhasil ditambahkan', res_mhs.data)

        res_dsn = self.client.post(
            '/master/dosen/add',
            data={'username': 'dosen_uji', 'nim_nip': '19900101', 'name': 'Dosen Uji', 'role': 'dosen', 'password': 'dosen123'},
            follow_redirects=True,
        )
        self.assertIn(b'berhasil ditambahkan', res_dsn.data)
        self._logout()

        # Super Admin creates & manages users
        self._login('superadmin', 'superadmin123')
        res_user = self.client.post(
            '/admin/users/add',
            data={
                'username': 'operator_baru',
                'nim_nip': 'OP-01',
                'name': 'Operator Baru',
                'email': 'op@uinjkt.ac.id',
                'password': 'op123',
                'role': 'admin_akademik',
            },
            follow_redirects=True,
        )
        self.assertIn(b'berhasil ditambahkan', res_user.data)

        with self.app.app_context():
            super_user = get_user_by_username('superadmin')
        res_self_del = self.client.post(f"/admin/users/delete/{super_user['id']}", follow_redirects=True)
        self.assertIn(b'Tidak dapat menghapus akun yang sedang login', res_self_del.data)

    def test_legacy_db_upgrades_to_rbac_schema_and_accounts(self):
        legacy_fd, legacy_path = tempfile.mkstemp(suffix='.db')
        os.close(legacy_fd)
        try:
            raw = sqlite3.connect(legacy_path)
            raw.execute('''
            CREATE TABLE users (
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
            raw.execute('''
            INSERT INTO users (username, password, name, nim_nip, role, prodi, ipk, semester)
            VALUES ('1251420999', '123456', 'IHSAN MUBAROK', '1251420999', 'mahasiswa', 'TI', 3.75, 6)
            ''')
            raw.commit()
            raw.close()

            init_db(db_path=legacy_path, database_url=None)
            legacy_app = create_app({'TESTING': True, 'DATABASE_URL': None, 'DATABASE_PATH': legacy_path, 'SECRET_KEY': 'k'})
            client = legacy_app.test_client()
            res = client.post('/login', data={'identifier': 'superadmin', 'password': 'superadmin123'}, follow_redirects=True)
            self.assertIn(b'Manajemen Pengguna', res.data)
            res2 = client.post('/logout', follow_redirects=True)
            self.assertIn(b'berhasil logout', res2.data)
            res3 = client.post('/login', data={'identifier': '1084729301', 'password': 'mhs123'}, follow_redirects=True)
            self.assertIn(b'IHSAN MUBAROK', res3.data)
            self.assertIn(b'1084729301', res3.data)
        finally:
            for ext in ('', '-wal', '-shm'):
                p = f'{legacy_path}{ext}'
                if os.path.exists(p):
                    os.unlink(p)

    def test_sa_rules_modal_only_visible_for_mahasiswa_role(self):
        # Mahasiswa sees modal, content, button, and sessionStorage script
        self._login('1084729301', 'mhs123')
        for path in ('/', '/krs'):
            html = self.client.get(path).data.decode('utf-8')
            self.assertIn('id="saRulesModal"', html)
            self.assertIn('Ketentuan Semester Antara (FST UIN Jakarta)', html)
            self.assertIn('Minimal Semester 4, disetujui Dosen PA', html)
            self.assertIn('Tidak wajib, maksimal 9 SKS', html)
            self.assertIn('Offline (luring) 16 pertemuan termasuk UTS &amp; UAS', html)
            self.assertIn('Cek jadwal Prodi', html)
            self.assertIn('Saya Mengerti', html)
            self.assertIn('Lihat Aturan SA', html)
            self.assertIn('sessionStorage.getItem(storageKey)', html)
        self._logout()

        # Non-Mahasiswa roles NEVER see the modal, button, or script
        for username, pw in (
            ('dosen1', 'dosen123'),
            ('kaprodi', 'kaprodi123'),
            ('admin_tu', 'admin123'),
            ('superadmin', 'superadmin123'),
        ):
            self._login(username, pw)
            html = self.client.get('/').data.decode('utf-8')
            self.assertNotIn('id="saRulesModal"', html, f'Modal leaked to {username}')
            self.assertNotIn('Lihat Aturan SA', html, f'Button leaked to {username}')
            self.assertNotIn('Ketentuan Semester Antara (FST UIN Jakarta)', html)
            self._logout()

        # Super Admin visiting /krs also should not see Mahasiswa-only modal
        self._login('superadmin', 'superadmin123')
        krs_html = self.client.get('/krs').data.decode('utf-8')
        self.assertNotIn('id="saRulesModal"', krs_html)
        self._logout()

    def test_mahasiswa_home_shows_catalog_instead_of_module_table(self):
        self._login('1084729301', 'mhs123')
        home_res = self.client.get('/')
        self.assertEqual(home_res.status_code, 200)
        home_html = home_res.data.decode('utf-8')
        self.assertIn('Informasi Matakuliah Ditawarkan', home_html)
        self.assertIn('Paket Semester 1', home_html)
        self.assertIn('Lanjut Memilih Mata Kuliah di KRS', home_html)
        self.assertNotIn('Daftar Modul &amp; Layanan Tersedia', home_html)
        self.assertNotIn('Daftar Modul & Layanan Tersedia', home_html)

        filtered_res = self.client.get('/?prodi=55')
        self.assertEqual(filtered_res.status_code, 200)
        filtered_html = filtered_res.data.decode('utf-8')
        self.assertRegex(filtered_html, r'<option[^>]*value="55"[^>]*selected')

        katalog_res = self.client.get('/katalog')
        self.assertEqual(katalog_res.status_code, 200)
        katalog_html = katalog_res.data.decode('utf-8')
        self.assertIn('Informasi Matakuliah Ditawarkan', katalog_html)
        self._logout()

        for username, password in [
            ('dosen1', 'dosen123'),
            ('kaprodi', 'kaprodi123'),
            ('admin_tu', 'admin123'),
            ('superadmin', 'superadmin123'),
        ]:
            self._login(username, password)
            role_home = self.client.get('/').data.decode('utf-8')
            self.assertIn('Daftar Modul', role_home, f'Module table missing for {username}')
            self.assertNotIn(
                'Informasi Matakuliah Ditawarkan',
                role_home,
                f'Mahasiswa catalog leaked to {username}',
            )
            self._logout()


if __name__ == '__main__':
    unittest.main()
