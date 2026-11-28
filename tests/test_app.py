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
from services import (
    create_user,
    get_courses_list,
    get_user_by_username,
    submit_student_krs,
    sync_invoices_for_ready_applications,
)


class SemesterAntaraPdfWorkflowTestCase(unittest.TestCase):
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
                student={
                    'nim_nip': '1084729301',
                    'name': 'IHSAN',
                    'prodi': 'Teknik Informatika',
                    'semester': 6,
                    'ipk': 3.75,
                    'dpa_name': 'Anif Hanifa Setianingrum, M.Si.',
                    'dpa_nip': '197904102006042001',
                },
                app={
                    'id': 1,
                    'total_sks': 3,
                    'submitted_at': datetime.datetime(2026, 11, 26, 8, 30, 0),
                    'verified_at': datetime.datetime(2026, 11, 26, 9, 0, 0),
                },
                items=[],
                invoice={'va_number': '8871729301123456', 'bank_name': 'BSI'},
            )
        self.assertIn('Ciputat, 2026-11-26', html)
        self.assertIn('Anif Hanifa Setianingrum, M.Si.', html)

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

    def test_unauthenticated_protection_and_login_page_6_demo_accounts(self):
        with self.client.get('/health') as res_health:
            self.assertEqual(res_health.status_code, 200)
            self.assertEqual(res_health.get_json(), {'status': 'ok'})

        with self.client.get('/login') as res_login:
            self.assertEqual(res_login.status_code, 200)
            for marker in (
                b'1084729301', b'mahasiswa@uinjkt.ac.id', b'mhs123',
                b'dpa1', b'dpa@uinjkt.ac.id', b'dpa123',
                b'dosen1', b'dosen@uinjkt.ac.id', b'dosen123',
                b'prodi', b'prodi@uinjkt.ac.id', b'prodi123',
                b'keuangan', b'keuangan@uinjkt.ac.id', b'keuangan123',
                b'superadmin', b'superadmin@uinjkt.ac.id', b'superadmin123',
            ):
                self.assertIn(marker, res_login.data)

        for static_path, mime_fragment in {
            '/static/css/app.css': 'text/css',
            '/static/js/bootstrap.min.js': 'javascript',
            '/static/img/logo_client.png': 'image/png',
        }.items():
            with self.client.get(static_path) as res_static:
                self.assertEqual(res_static.status_code, 200)
                self.assertIn(mime_fragment, res_static.content_type)

        for protected_path in (
            '/', '/katalog', '/usulan', '/krs', '/tagihan',
            '/dpa', '/dosen',
            '/prodi/pengumuman', '/prodi/periode', '/prodi/usulan',
            '/prodi/katalog', '/prodi/monitoring', '/prodi/rekap',
            '/keuangan/tarif', '/keuangan/pembayaran',
            '/master/mahasiswa', '/master/prodi', '/admin/users',
        ):
            res = self.client.get(protected_path)
            self.assertEqual(res.status_code, 302, f'Expected redirect on {protected_path}')
            self.assertIn('/login', res.headers['Location'])

    def test_login_by_username_or_email_wrong_password_and_logout(self):
        res_bad = self._login('1084729301', 'salah')
        self.assertIn(b'Username/email atau password salah', res_bad.data)
        self.assertEqual(self.client.get('/').status_code, 302)

        res_dpa = self._login('dpa@uinjkt.ac.id', 'dpa123')
        self.assertEqual(res_dpa.status_code, 200)
        self.assertIn(b'Dosen Pembimbing Akademik (DPA)', res_dpa.data)

        res_out = self._logout()
        self.assertIn(b'berhasil logout', res_out.data)
        self.assertEqual(self.client.get('/').status_code, 302)

        res_open = self.client.post(
            '/login',
            data={'identifier': 'prodi@uinjkt.ac.id', 'password': 'prodi123', 'next': '//evil.com'},
        )
        self.assertEqual(res_open.status_code, 302)
        self.assertFalse(res_open.headers['Location'].startswith('//evil.com'))

    def test_rbac_menu_and_direct_url_boundaries_for_all_6_roles(self):
        # 1. Mahasiswa
        self._login('1084729301', 'mhs123')
        for allowed in ('/', '/katalog', '/usulan', '/krs', '/tagihan'):
            self.assertEqual(self.client.get(allowed).status_code, 200)
        for forbidden in ('/dpa', '/dosen', '/prodi/monitoring', '/prodi/katalog', '/keuangan/pembayaran', '/master/mahasiswa', '/admin/users'):
            res = self.client.get(forbidden, follow_redirects=True)
            self.assertIn(b'Akses ditolak', res.data, f'Mahasiswa should be blocked from {forbidden}')
        self._logout()

        # 2. DPA (Dosen Pembimbing Akademik)
        self._login('dpa1', 'dpa123')
        self.assertEqual(self.client.get('/dpa').status_code, 200)
        for forbidden in ('/krs', '/usulan', '/dosen', '/prodi/monitoring', '/keuangan/pembayaran', '/master/mahasiswa', '/admin/users'):
            res = self.client.get(forbidden, follow_redirects=True)
            self.assertIn(b'Akses ditolak', res.data, f'DPA should be blocked from {forbidden}')
        self._logout()

        # 3. Dosen Pengampu
        self._login('dosen1', 'dosen123')
        self.assertEqual(self.client.get('/dosen').status_code, 200)
        for forbidden in ('/krs', '/dpa', '/prodi/monitoring', '/prodi/katalog', '/keuangan/pembayaran', '/admin/users'):
            res = self.client.get(forbidden, follow_redirects=True)
            self.assertIn(b'Akses ditolak', res.data, f'Dosen should be blocked from {forbidden}')
        self._logout()

        # 4. Program Studi / Admin Prodi
        self._login('prodi', 'prodi123')
        for allowed in ('/prodi/pengumuman', '/prodi/periode', '/prodi/usulan', '/prodi/katalog', '/prodi/jadwal_ruang', '/prodi/monitoring', '/prodi/rekap'):
            self.assertEqual(self.client.get(allowed).status_code, 200, f'Prodi failed on {allowed}')
        for forbidden in ('/krs', '/dpa', '/dosen', '/keuangan/tarif', '/keuangan/pembayaran', '/master/mahasiswa', '/admin/users'):
            res = self.client.get(forbidden, follow_redirects=True)
            self.assertIn(b'Akses ditolak', res.data, f'Prodi should be blocked from {forbidden}')
        self._logout()

        # 5. Bagian Keuangan
        self._login('keuangan', 'keuangan123')
        for allowed in ('/keuangan/tarif', '/keuangan/pembayaran'):
            self.assertEqual(self.client.get(allowed).status_code, 200)
        for forbidden in ('/krs', '/dpa', '/dosen', '/prodi/katalog', '/prodi/monitoring', '/master/mahasiswa', '/admin/users'):
            res = self.client.get(forbidden, follow_redirects=True)
            self.assertIn(b'Akses ditolak', res.data, f'Keuangan should be blocked from {forbidden}')
        self._logout()

        # 6. Super Admin
        self._login('superadmin', 'superadmin123')
        for allowed in (
            '/', '/katalog', '/usulan', '/krs', '/dpa', '/dosen',
            '/prodi/pengumuman', '/prodi/periode', '/prodi/usulan', '/prodi/katalog',
            '/prodi/monitoring', '/prodi/rekap',
            '/keuangan/tarif', '/keuangan/pembayaran',
            '/master/mahasiswa', '/master/dosen', '/master/prodi', '/admin/users',
        ):
            self.assertEqual(self.client.get(allowed).status_code, 200, f'Superadmin failed on {allowed}')
        self._logout()

    def test_seeded_catalog_programs_and_10_quota_ready_classes(self):
        with self.app.app_context():
            ti_courses = get_courses_list(prodi_code='60')
            all_courses = get_courses_list(prodi_code='ALL')
            by_code = {c['code']: c for c in all_courses}

        self.assertEqual(len(ti_courses), 45)
        self.assertGreaterEqual(len(all_courses), 49)
        self.assertEqual(by_code['FST6091108']['approved_count'], 10)
        self.assertEqual(by_code['FST6091103']['approved_count'], 10)

    def test_sk_rektor_686_validation_and_fr06_edit_cancel(self):
        with self.app.app_context():
            courses = get_courses_list(prodi_code='ALL')
            by_code = {c['code']: c for c in courses}
            ihsan = get_user_by_username('1084729301')
            bagas = get_user_by_username('1072918463')  # IPK 2.85 < 3.00

            # Semester < 4 rejected
            create_user('1011223344', 'mhs123', 'MABA SEM 2', '1011223344', 'mahasiswa', 'Teknik Informatika', semester=2, ipk=3.80)
            maba = get_user_by_username('1011223344')
            ok, msg = submit_student_krs(maba['id'], [{'course_id': by_code['FST6091101']['id'], 'jenis_pengambilan': 'Mata Kuliah Baru'}])
            self.assertFalse(ok)
            self.assertIn('Semester 4', msg)

            # Sanksi akademik rejected
            create_user('1011223355', 'mhs123', 'MHS SANKSI', '1011223355', 'mahasiswa', 'Teknik Informatika', semester=6, ipk=3.80, status_sanksi='Sedang Sanksi')
            sanksi = get_user_by_username('1011223355')
            ok, msg = submit_student_krs(sanksi['id'], [{'course_id': by_code['FST6091101']['id'], 'jenis_pengambilan': 'Mata Kuliah Baru'}])
            self.assertFalse(ok)
            self.assertIn('sanksi akademik', msg)

            # Perbaikan on grade A rejected (Auto-Check 1 / Alur Eksepsi 6a.d)
            ok, msg = submit_student_krs(
                ihsan['id'],
                [{'course_id': by_code['UIN6014203']['id'], 'jenis_pengambilan': 'Perbaikan Nilai'}],
            )
            self.assertFalse(ok)
            self.assertIn('C+, C, C-, D, atau E', msg)

            # MK Baru with IPK < 3.00 rejected (Bagas IPK 2.85)
            ok, msg = submit_student_krs(
                bagas['id'],
                [{'course_id': by_code['FST6091102']['id'], 'jenis_pengambilan': 'Mata Kuliah Baru'}],
            )
            self.assertFalse(ok)
            self.assertIn('IPK minimal 3,00', msg)

            # Bagas CAN still take Perbaikan Nilai (grade D in FST6091101)
            ok, msg = submit_student_krs(
                bagas['id'],
                [{'course_id': by_code['FST6091101']['id'], 'jenis_pengambilan': 'Perbaikan Nilai'}],
            )
            self.assertTrue(ok, msg)

        # FR-06: IHSAN submits KRS, modifies choice before closure, then cancels cleanly
        self._login('1084729301', 'mhs123')
        c1 = by_code['FST6091101']['id']
        c2 = by_code['FST6091125']['id']
        res1 = self.client.post('/krs/submit', data={'course_ids': [c1], f'jenis_{c1}': 'Perbaikan Nilai', 'preferred_bank': 'BNI'}, follow_redirects=True)
        self.assertIn(b'berhasil dikirim', res1.data)

        # Modify while still 'Buka' (FR-06)
        res2 = self.client.post('/krs/submit', data={'course_ids': [c1, c2], f'jenis_{c1}': 'Perbaikan Nilai', f'jenis_{c2}': 'Perbaikan Nilai', 'preferred_bank': 'BSI'}, follow_redirects=True)
        self.assertIn(b'berhasil dikirim', res2.data)

        # Cancel while 'Buka' (FR-06)
        res_cancel = self.client.post('/krs/cancel', follow_redirects=True)
        self.assertIn(b'berhasil dibatalkan', res_cancel.data)

    def test_full_pdf_workflow_dpa_prodi_dosen_dispensasi_keuangan_and_expired(self):
        with self.app.app_context():
            courses = get_courses_list(prodi_code='ALL')
            by_code = {c['code']: c for c in courses}
            ihsan = get_user_by_username('1084729301')

        # 1. Mahasiswa submits cross-prodi proposal (AD-01) and submits KRS (6 SKS: FST6091108 >=10, FST6091101 <10)
        self._login('1084729301', 'mhs123')
        res_prop = self.client.post(
            '/usulan',
            data={
                'is_cross_prodi': '1',
                'target_prodi_code': '55',
                'course_code': 'SIS6091999',
                'course_name': 'Big Data Enterprise',
                'sks': '3',
                'semester_target': '5',
                'origin_course_code': 'FST6091912',
                'origin_course_name': 'Data Science',
                'syllabus_summary': 'Spark, Hadoop, data lake architecture 16 pertemuan.',
                'reason': 'Ekuivalensi pilihan peminatan data.',
            },
            follow_redirects=True,
        )
        self.assertIn(b'berhasil dikirim ke Program Studi', res_prop.data)

        c_big = by_code['FST6091108']['id']    # 10 DPA-approved -> >= 10 quota (Senin 08.00)
        c_small = by_code['FST6091106']['id']  # < 10 quota, taught by dosen1 (Kamis 13.00), total 7 SKS
        res_krs = self.client.post(
            '/krs/submit',
            data={
                'course_ids': [c_big, c_small],
                f'jenis_{c_big}': 'Perbaikan Nilai',
                f'jenis_{c_small}': 'Perbaikan Nilai',
                'preferred_bank': 'BSI',
            },
            follow_redirects=True,
        )
        self.assertIn(b'verifikasi Dosen Pembimbing Akademik', res_krs.data)

        with self.app.app_context():
            conn = get_db()
            try:
                app_row = conn.execute("SELECT * FROM krs_applications WHERE student_id = ?", (ihsan['id'],)).fetchone()
                prop_row = conn.execute("SELECT * FROM course_proposals WHERE course_code = 'SIS6091999'").fetchone()
            finally:
                conn.close()
        app_id = app_row['id']
        self._logout()

        # 2. DPA (dpa1) rejects first (BR-04), IHSAN re-submits, then DPA approves WITHOUT creating premature VA (BR-08)!
        self._login('dpa1', 'dpa123')
        res_dpa_list = self.client.get('/dpa')
        self.assertIn(b'IHSAN MUBAROK', res_dpa_list.data)
        self.assertIn(b'DANUARDI SAPUTRO', res_dpa_list.data)
        res_reject = self.client.post(f'/dpa/reject/{app_id}', data={'notes': 'Silakan konsultasi SKS terlebih dahulu.'}, follow_redirects=True)
        self.assertIn(b'DITOLAK DPA', res_reject.data)
        self._logout()

        # Mahasiswa revises & resubmits (FR-05)
        self._login('1084729301', 'mhs123')
        self.client.post(
            '/krs/submit',
            data={
                'course_ids': [c_big, c_small],
                f'jenis_{c_big}': 'Perbaikan Nilai',
                f'jenis_{c_small}': 'Perbaikan Nilai',
                'preferred_bank': 'BSI',
            },
            follow_redirects=True,
        )
        self._logout()

        # DPA approves -> BR-08: NO invoice yet because registration is still open & classes not finalized!
        self._login('dpa1', 'dpa123')
        res_acc = self.client.post(f'/dpa/approve/{app_id}', follow_redirects=True)
        self.assertIn(b'DISETUJUI DPA', res_acc.data)
        with self.app.app_context():
            conn = get_db()
            try:
                inv_early = conn.execute("SELECT * FROM invoices WHERE application_id = ?", (app_id,)).fetchone()
            finally:
                conn.close()
        self.assertIsNone(inv_early, 'BR-08 violated: invoice should NOT exist before registration close & class confirmation!')
        self._logout()

        # 3. Prodi approves proposal, tests UC-PRD-07 Eksepsi 1a lock before closure, then closes registration
        self._login('prodi', 'prodi123')
        with self.app.app_context():
            dosen1 = get_user_by_username('dosen1')
        res_rev_prop = self.client.post(
            f"/prodi/usulan/review/{prop_row['id']}",
            data={'decision': 'approve', 'publish_to_catalog': '1', 'lecturer_id': dosen1['id'], 'admin_notes': 'Ekuivalen disetujui'},
            follow_redirects=True,
        )
        self.assertIn(b'diterbitkan ke Katalog Resmi', res_rev_prop.data)

        # Eksepsi 1a UC-PRD-07: cannot set class 'Dibuka' before closing registration
        res_early_open = self.client.post(f'/prodi/status/{c_big}', data={'status': 'Dibuka'}, follow_redirects=True)
        self.assertIn(b'dinonaktifkan sebelum periode pendaftaran ditutup', res_early_open.data)

        # Close registration (Auto-Check 3) -> < 10 becomes 'Menunggu Kebijakan Prodi'
        res_tutup = self.client.post('/prodi/tutup', follow_redirects=True)
        self.assertIn(b'resmi DITUTUP', res_tutup.data)

        # Open regular >= 10 class FST6091108 -> 'Dibuka'
        res_open_big = self.client.post(f'/prodi/status/{c_big}', data={'status': 'Dibuka'}, follow_redirects=True)
        self.assertIn(b'berhasil ditetapkan menjadi: Dibuka', res_open_big.data)

        # Request dispensation for small class FST6091106 (< 10) -> cannot finalize before lecturer agrees
        res_req_disp = self.client.post(f'/prodi/dispensasi/request/{c_small}', follow_redirects=True)
        self.assertIn(b'dikirim ke dasbor Dosen Pengampu', res_req_disp.data)
        res_premature_disp = self.client.post(f'/prodi/status/{c_small}', data={'status': 'Dispensasi Buka'}, follow_redirects=True)
        self.assertIn(b'belum mengonfirmasi', res_premature_disp.data)
        self._logout()

        # 4. Dosen Pengampu confirms FR-10 regular class (TIF3104) & FR-11 dispensation (FST6091106)
        self._login('dosen1', 'dosen123')
        self.client.post(f"/dosen/confirm/{by_code['TIF3104']['id']}", data={'agreed': '1'}, follow_redirects=True)
        res_disp_acc = self.client.post(f'/dosen/dispensasi/{c_small}', data={'agreed': '1'}, follow_redirects=True)
        self.assertIn(b'BERSEDIA MENGAJAR KELAS DISPENSASI', res_disp_acc.data)
        self._logout()

        # 5. Prodi finalizes Dispensasi Buka -> BR-08 immediately issues VA for IHSAN (7 SKS * 220000 = 1.540.000, BSI)!
        self._login('prodi', 'prodi123')
        res_disp_open = self.client.post(f'/prodi/status/{c_small}', data={'status': 'Dispensasi Buka'}, follow_redirects=True)
        self.assertIn(b'Dispensasi Buka', res_disp_open.data)

        with self.app.app_context():
            conn = get_db()
            try:
                inv = conn.execute("SELECT * FROM invoices WHERE application_id = ?", (app_id,)).fetchone()
            finally:
                conn.close()
        self.assertIsNotNone(inv)
        self.assertEqual(inv['bank_name'], 'BSI')
        self.assertEqual(inv['amount'], 7 * 220000)
        self._logout()

        # 6. Bagian Keuangan reconciles payment to Lunas (Auto-Check 4)
        self._login('keuangan', 'keuangan123')
        res_pay = self.client.post(
            f"/keuangan/rekonsiliasi/{inv['id']}",
            data={'ref_no': 'BSI-REF-2026-01', 'notes': 'Lunas test'},
            follow_redirects=True,
        )
        self.assertIn(b'DIREKONSILIASI LUNAS', res_pay.data)

        # Also open FST6091103 & test BR-10 Expired on one of the 10 seeded approved students
        self._logout()
        self._login('prodi', 'prodi123')
        c_sbd = by_code['FST6091103']['id']
        self.client.post(f'/prodi/status/{c_sbd}', data={'status': 'Dibuka'}, follow_redirects=True)
        self._logout()

        self._login('keuangan', 'keuangan123')
        self.client.post('/keuangan/sync_va', follow_redirects=True)
        with self.app.app_context():
            stu1 = get_user_by_username('1051900001')
            conn = get_db()
            try:
                stu1_inv = conn.execute("SELECT * FROM invoices WHERE student_id = ?", (stu1['id'],)).fetchone()
            finally:
                conn.close()
        self.assertIsNotNone(stu1_inv)
        res_exp = self.client.post(f"/keuangan/expire/{stu1_inv['id']}", follow_redirects=True)
        self.assertIn(b'EXPIRED', res_exp.data)
        self._logout()

        # 7. Dosen Pengampu now sees IHSAN as official paid participant (FR-12)
        self._login('dosen1', 'dosen123')
        dosen_html = self.client.get('/dosen').data.decode('utf-8')
        self.assertIn('IHSAN MUBAROK', dosen_html)
        self._logout()

        # 8. Mahasiswa prints Official KRS showing dynamic DPA signature!
        self._login('1084729301', 'mhs123')
        res_print = self.client.get('/cetak_krs')
        self.assertEqual(res_print.status_code, 200)
        self.assertIn(b'KARTU RENCANA STUDI (KRS) SAH', res_print.data)
        self.assertIn(b'Anif Hanifa Setianingrum, M.Si.', res_print.data)

    def test_ilmu_kesehatan_rate_and_superadmin_master_crud(self):
        with self.app.app_context():
            create_user('1070000001', 'mhs123', 'MHS KEDOKTERAN', '1070000001', 'mahasiswa', 'Pendidikan Dokter', prodi_code='70', ipk=3.60, semester=6)
            med_stu = get_user_by_username('1070000001')
            med_course = [c for c in get_courses_list(prodi_code='70')][0]
            ok, msg = submit_student_krs(med_stu['id'], [{'course_id': med_course['id'], 'jenis_pengambilan': 'Mata Kuliah Baru'}])
            self.assertTrue(ok, msg)

        self._login('dpa1', 'dpa123')
        with self.app.app_context():
            conn = get_db()
            try:
                med_app = conn.execute("SELECT id FROM krs_applications WHERE student_id = ?", (med_stu['id'],)).fetchone()
            finally:
                conn.close()
        self.client.post(f"/dpa/approve/{med_app['id']}", follow_redirects=True)
        self._logout()

        self._login('prodi', 'prodi123')
        self.client.post('/prodi/tutup', follow_redirects=True)
        self._logout()

        self._login('dosen1', 'dosen123')
        # Set lecturer_id temporarily not needed if prodi requests after assigning, test dispensasi via superadmin
        self._logout()

        self._login('superadmin', 'superadmin123')
        self.client.post(f"/dosen/dispensasi/{med_course['id']}", data={'agreed': '1'}, follow_redirects=True)
        self.client.post(f"/prodi/status/{med_course['id']}", data={'status': 'Dispensasi Buka'}, follow_redirects=True)
        with self.app.app_context():
            sync_invoices_for_ready_applications()
            conn = get_db()
            try:
                med_inv = conn.execute("SELECT * FROM invoices WHERE application_id = ?", (med_app['id'],)).fetchone()
            finally:
                conn.close()
        self.assertIsNotNone(med_inv)
        self.assertEqual(med_inv['amount'], 3 * 850000)

        # Super Admin manages master prodi & grades
        res_prodi = self.client.post(
            '/master/prodi/add',
            data={'code': '81', 'name': 'Farmasi', 'faculty': 'FIKES', 'rumpun_ilmu': 'Ilmu Kesehatan', 'status_buka_sa': 'Menyelenggarakan'},
            follow_redirects=True,
        )
        self.assertIn(b'berhasil ditambahkan', res_prodi.data)

    def test_legacy_db_upgrades_to_6_roles_and_pdf_schema(self):
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
            for uname, pw, marker in (
                ('dpa1', 'dpa123', b'Dosen Pembimbing Akademik'),
                ('prodi', 'prodi123', b'Program Studi'),
                ('keuangan', 'keuangan123', b'Bagian Keuangan'),
                ('1084729301', 'mhs123', b'IHSAN MUBAROK'),
            ):
                res = client.post('/login', data={'identifier': uname, 'password': pw}, follow_redirects=True)
                self.assertIn(marker, res.data)
                client.get('/logout')
        finally:
            for ext in ('', '-wal', '-shm'):
                p = f'{legacy_path}{ext}'
                if os.path.exists(p):
                    os.unlink(p)

    def test_sa_rules_modal_only_visible_for_mahasiswa_role(self):
        self._login('1084729301', 'mhs123')
        for path in ('/', '/krs'):
            html = self.client.get(path).data.decode('utf-8')
            self.assertIn('id="saRulesModal"', html)
            self.assertIn('Ketentuan Semester Antara (FST UIN Jakarta)', html)
            self.assertIn('Minimal Semester 4, disetujui Dosen PA', html)
            self.assertIn('Saya Mengerti', html)
            self.assertIn('Lihat Aturan SA', html)
            self.assertIn('sessionStorage.getItem(storageKey)', html)
        self._logout()

        for username, pw in (
            ('dpa1', 'dpa123'),
            ('dosen1', 'dosen123'),
            ('prodi', 'prodi123'),
            ('keuangan', 'keuangan123'),
            ('superadmin', 'superadmin123'),
        ):
            self._login(username, pw)
            html = self.client.get('/').data.decode('utf-8')
            self.assertNotIn('id="saRulesModal"', html, f'Modal leaked to {username}')
            self.assertNotIn('Lihat Aturan SA', html, f'Button leaked to {username}')
            self._logout()

        self._login('superadmin', 'superadmin123')
        self.assertNotIn('id="saRulesModal"', self.client.get('/krs').data.decode('utf-8'))
        self._logout()

    def test_mahasiswa_home_shows_announcements_and_filtered_catalog_instead_of_module_table(self):
        self._login('1084729301', 'mhs123')
        home_res = self.client.get('/')
        self.assertEqual(home_res.status_code, 200)
        home_html = home_res.data.decode('utf-8')
        self.assertIn('Pengumuman Resmi Program Studi', home_html)
        self.assertIn('Informasi Matakuliah Ditawarkan', home_html)
        self.assertIn('Paket Semester 1', home_html)
        self.assertNotIn('Daftar Modul &amp; Layanan Tersedia', home_html)
        self.assertNotIn('Daftar Modul & Layanan Tersedia', home_html)

        # Real Prodi filter works: prodi=55 shows Sistem Informasi cross-prodi course
        filtered_html = self.client.get('/?prodi=55').data.decode('utf-8')
        self.assertRegex(filtered_html, r'<option[^>]*value="55"[^>]*selected')
        self.assertIn('SIS6091103', filtered_html)
        self.assertNotIn('FST6091101', filtered_html)
        self._logout()

        for username, password in [
            ('dpa1', 'dpa123'),
            ('dosen1', 'dosen123'),
            ('prodi', 'prodi123'),
            ('keuangan', 'keuangan123'),
            ('superadmin', 'superadmin123'),
        ]:
            self._login(username, password)
            role_home = self.client.get('/').data.decode('utf-8')
            self.assertIn('Daftar Modul', role_home, f'Module table missing for {username}')
            self.assertNotIn('Informasi Matakuliah Ditawarkan', role_home)
            self._logout()


if __name__ == '__main__':
    unittest.main()
