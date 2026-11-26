import datetime
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from flask import render_template

from app import create_app
from config import _resolve_db_path, normalize_database_url
from database import get_db, translate_placeholders
from services import get_courses_list, get_user_by_username


class SemesterAntaraTestCase(unittest.TestCase):
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
                student={'nim_nip': '1251420125', 'name': 'IHSAN', 'prodi': 'TI', 'semester': 6, 'ipk': 3.75, 'dpa_name': 'Dr. Dewi'},
                app={'id': 1, 'total_sks': 3, 'submitted_at': datetime.datetime(2026, 11, 26, 8, 30, 0), 'verified_at': datetime.datetime(2026, 11, 26, 9, 0, 0)},
                items=[],
                invoice={'va_number': '8871420125123456'},
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

    def test_health_and_home_and_static_assets(self):
        with self.client.get('/health') as res_health:
            self.assertEqual(res_health.status_code, 200)
            self.assertEqual(res_health.get_json(), {'status': 'ok'})

        with self.client.get('/') as res_home:
            self.assertEqual(res_home.status_code, 200)
            self.assertIn(b'Sistem Terpusat Pengajuan Semester Antara', res_home.data)

        expected_mime_fragments = {
            '/static/css/app.css': 'text/css',
            '/static/css/bootstrap.min.css': 'text/css',
            '/static/js/jquery-2.2.3.min.js': 'javascript',
            '/static/js/bootstrap.min.js': 'javascript',
            '/static/img/logo_client.png': 'image/png',
        }
        for static_path, mime_fragment in expected_mime_fragments.items():
            with self.client.get(static_path) as res_static:
                self.assertEqual(res_static.status_code, 200, f'Failed static asset: {static_path}')
                self.assertIn(mime_fragment, res_static.content_type)

    def test_seeded_catalog_has_all_45_courses(self):
        with self.app.app_context():
            courses = get_courses_list()
        self.assertEqual(len(courses), 45)

    def test_role_switching_and_dashboards_render(self):
        for role in ('mahasiswa', 'dpa', 'dosen', 'prodi', 'keuangan'):
            res = self.client.get(f'/switch_role/{role}', follow_redirects=True)
            self.assertEqual(res.status_code, 200)

        for path in (
            '/katalog',
            '/krs',
            '/tagihan',
            '/dpa',
            '/dosen',
            '/prodi/periode',
            '/prodi/katalog',
            '/prodi/jadwal_ruang',
            '/prodi/monitoring',
            '/prodi/rekap',
            '/keuangan/tarif',
            '/keuangan/pembayaran',
        ):
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f'Route failed: {path}')

    def test_krs_validation_max_sks_schedule_conflict_and_quota(self):
        with self.app.app_context():
            courses = get_courses_list()
            by_code = {c['code']: c for c in courses}

        res_conflict = self.client.post(
            '/krs/submit',
            data={'course_ids': [by_code['FST6091101']['id'], by_code['TIF3101']['id']]},
            follow_redirects=True,
        )
        self.assertIn(b'bentrok jadwal', res_conflict.data)

        res_over_sks = self.client.post(
            '/krs/submit',
            data={
                'course_ids': [
                    by_code['FST6094102']['id'],
                    by_code['UIN6033201']['id'],
                    by_code['FST6091101']['id'],
                ]
            },
            follow_redirects=True,
        )
        self.assertIn(b'melebihi batas maksimal 9 SKS', res_over_sks.data)

        target_course_id = by_code['FST6091108']['id']
        with self.app.app_context():
            conn = get_db()
            try:
                conn.execute("UPDATE courses SET quota = 1 WHERE id = ?", (target_course_id,))
                conn.commit()
            finally:
                conn.close()

        res_full = self.client.post(
            '/krs/submit',
            data={'course_ids': [target_course_id]},
            follow_redirects=True,
        )
        self.assertIn(b'sudah penuh', res_full.data)

    def test_end_to_end_krs_approval_payment_print_and_cancel(self):
        with self.app.app_context():
            courses = get_courses_list()
            by_code = {c['code']: c for c in courses}
            student = get_user_by_username('1251420125')

        res_print_blocked = self.client.get('/cetak_krs', follow_redirects=True)
        self.assertIn(b'status pembayaran lunas', res_print_blocked.data)

        c1_id = by_code['FST6091101']['id']
        c2_id = by_code['FST6091125']['id']
        res_submit = self.client.post(
            '/krs/submit',
            data={'course_ids': [c1_id, c2_id]},
            follow_redirects=True,
        )
        self.assertEqual(res_submit.status_code, 200)
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
        self.assertIsNotNone(app_row)
        self.assertEqual(app_row['status'], 'Diajukan')
        app_id = app_row['id']

        res_reject = self.client.post(
            f'/dpa/reject/{app_id}',
            data={'notes': 'Tambahkan MK lain jika perlu.'},
            follow_redirects=True,
        )
        self.assertIn(b'DITOLAK', res_reject.data)

        res_resubmit = self.client.post(
            '/krs/submit',
            data={'course_ids': [c1_id, c2_id]},
            follow_redirects=True,
        )
        self.assertIn(b'berhasil diajukan', res_resubmit.data)

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
        self.assertEqual(inv['amount'], 6 * 220000)
        self.assertEqual(inv['status'], 'Belum Lunas')

        res_cancel = self.client.post(
            f'/prodi/status/{c2_id}',
            data={'status': 'Dibatalkan'},
            follow_redirects=True,
        )
        self.assertEqual(res_cancel.status_code, 200)
        with self.app.app_context():
            conn = get_db()
            try:
                updated_app = conn.execute(
                    "SELECT total_sks FROM krs_applications WHERE id = ?",
                    (app_id,),
                ).fetchone()
                updated_inv = conn.execute(
                    "SELECT amount FROM invoices WHERE id = ?",
                    (inv['id'],),
                ).fetchone()
            finally:
                conn.close()
        self.assertEqual(updated_app['total_sks'], 3)
        self.assertEqual(updated_inv['amount'], 3 * 220000)

        res_pay = self.client.post(
            f"/keuangan/rekonsiliasi/{inv['id']}",
            data={'ref_no': 'REF-TEST-001', 'notes': 'Lunas test'},
            follow_redirects=True,
        )
        self.assertIn(b'DIREKONSILIASI LUNAS', res_pay.data)

        res_print = self.client.get('/cetak_krs')
        self.assertEqual(res_print.status_code, 200)
        self.assertIn(b'KARTU RENCANA STUDI (KRS) SAH', res_print.data)

    def test_dosen_prodi_and_keuangan_workflows(self):
        with self.app.app_context():
            courses = get_courses_list()
            by_code = {c['code']: c for c in courses}
            dosen = get_user_by_username('dosen1')

        tif3104 = by_code['TIF3104']['id']
        res_confirm = self.client.post(
            f'/dosen/confirm/{tif3104}',
            data={'agreed': '1'},
            follow_redirects=True,
        )
        self.assertIn(b'BERSEDIA MENGAJAR', res_confirm.data)

        res_disp = self.client.post(
            f'/dosen/dispensasi/{tif3104}',
            data={'agreed': '1'},
            follow_redirects=True,
        )
        self.assertIn(b'BERSEDIA MENGAJAR KELAS DISPENSASI', res_disp.data)

        res_add = self.client.post(
            '/prodi/katalog/add',
            data={
                'code': 'TIF9999',
                'name': 'Komputasi Awan Terapan',
                'sks': '3',
                'quota': '25',
                'lecturer_id': str(dosen['id']),
                'schedule_day': 'Jumat',
                'schedule_time': '13.30 - 16.00 WIB',
                'room': 'Lab Cloud FST',
                'semester': '6',
                'class_name': '6ATI',
                'wp_type': 'P',
            },
            follow_redirects=True,
        )
        self.assertIn(b'TIF9999', res_add.data)

        res_dup = self.client.post(
            '/prodi/katalog/add',
            data={
                'code': 'TIF9999',
                'name': 'Duplikat',
                'sks': '3',
                'quota': '25',
                'lecturer_id': str(dosen['id']),
            },
            follow_redirects=True,
        )
        self.assertIn(b'sudah terdaftar', res_dup.data)

        res_close = self.client.post('/prodi/tutup', follow_redirects=True)
        self.assertIn(b'DITUTUP', res_close.data)
        res_open = self.client.post('/prodi/buka', follow_redirects=True)
        self.assertIn(b'DIBUKA', res_open.data)

        res_bad_tarif = self.client.post(
            '/keuangan/tarif/update',
            data={'sks_rate': 'abc'},
            follow_redirects=True,
        )
        self.assertIn(b'angka valid', res_bad_tarif.data)

        res_good_tarif = self.client.post(
            '/keuangan/tarif/update',
            data={'sks_rate': '250000'},
            follow_redirects=True,
        )
        self.assertIn(b'Rp250,000', res_good_tarif.data)

        res_csv = self.client.get('/prodi/export_csv')
        self.assertEqual(res_csv.status_code, 200)
        self.assertIn('text/csv', res_csv.content_type)
        self.assertIn(b'NIM;NAMA MAHASISWA', res_csv.data)


if __name__ == '__main__':
    unittest.main()
