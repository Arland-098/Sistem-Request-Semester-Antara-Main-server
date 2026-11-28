from database import get_db
from services.billing_service import PARTNER_BANKS, issue_invoice_if_eligible_in_tx
from services.config_service import get_config

ELIGIBLE_IMPROVEMENT_GRADES = ('C+', 'C', 'C-', 'D', 'E')


def submit_student_krs(
    student_id: int,
    course_selections: list,
    preferred_bank: str = 'Bank Mandiri',
) -> tuple[bool, str]:
    """
    UC-MHS-04, BR-03, Auto-Check 1 & 2, FR-06:
    Validasi lengkap SK Rektor 686/2025:
    1. Periode pendaftaran harus terbuka
    2. Mahasiswa aktif & bebas sanksi akademik
    3. Mahasiswa minimal semester 4
    4. Total beban SKS <= max_sks (9 SKS)
    5. Jenis pengambilan:
       - Perbaikan Nilai -> wajib nilai historis C+, C, C-, D, atau E
       - Mata Kuliah Baru (akselerasi) -> wajib IPK >= 3.00 dan belum lulus nilai A/B
    6. Anti-bentrok jadwal kuliah luring
    7. Proteksi kuota real-time dengan transaksi locking
    8. FR-06: Mendukung ubah pilihan sebelum pendaftaran ditutup
    """
    normalized_items: list[dict] = []
    seen_ids: set[int] = set()
    for entry in course_selections or []:
        if isinstance(entry, dict):
            cid = int(entry['course_id'])
            jenis = entry.get('jenis_pengambilan')
        else:
            cid = int(entry)
            jenis = None
        if cid not in seen_ids:
            seen_ids.add(cid)
            normalized_items.append({'course_id': cid, 'jenis_pengambilan': jenis})

    if not normalized_items:
        return False, "Pilih minimal 1 mata kuliah."

    chosen_bank = preferred_bank if preferred_bank in PARTNER_BANKS else 'Bank Mandiri'

    conn = get_db(isolation_level=None)
    in_tx = False
    try:
        conn.begin_exclusive()
        in_tx = True

        cfg_rows = conn.execute(
            """
            SELECT key, value FROM system_config
            WHERE key IN ('registration_status', 'active_semester', 'max_sks')
            """
        ).fetchall()
        cfg = {row['key']: row['value'] for row in cfg_rows}

        if cfg.get('registration_status', 'Buka') != 'Buka':
            conn.execute("ROLLBACK")
            in_tx = False
            return False, "Periode pendaftaran Semester Antara sudah ditutup. Formulir dikunci (Auto-Check 3)."

        student = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (student_id,),
        ).fetchone()
        if not student:
            conn.execute("ROLLBACK")
            in_tx = False
            return False, "Data profil mahasiswa tidak ditemukan."

        if (student['status_sanksi'] or 'Aktif Bebas Sanksi') != 'Aktif Bebas Sanksi':
            conn.execute("ROLLBACK")
            in_tx = False
            return False, (
                "Pengajuan ditolak (Auto-Check 1): Mahasiswa tercatat sedang menjalani sanksi akademik "
                "berdasarkan SK Rektor No. 686/2025."
            )

        if (student['semester'] or 0) < 4:
            conn.execute("ROLLBACK")
            in_tx = False
            return False, (
                f"Pengajuan ditolak (Auto-Check 1): Syarat minimal Semester 4 "
                f"(Anda saat ini berada pada Semester {student['semester']})."
            )

        active_semester = cfg.get('active_semester', 'Semester Antara 2026/2027')
        max_sks = int(cfg.get('max_sks', '9'))

        existing_app = conn.execute(
            '''
            SELECT id, status FROM krs_applications
            WHERE student_id = ? AND semester_period = ?
            ''',
            (student_id, active_semester),
        ).fetchone()

        if existing_app and existing_app['status'] in ('Lunas', 'Expired'):
            conn.execute("ROLLBACK")
            in_tx = False
            return False, (
                f"Pengajuan KRS Anda saat ini berstatus '{existing_app['status']}' dan tidak dapat diubah."
            )

        course_ids = [item['course_id'] for item in normalized_items]
        placeholders = ','.join('?' for _ in course_ids)
        lock_clause = " FOR UPDATE" if conn.is_postgres else ""
        selected_courses = conn.execute(
            f"SELECT * FROM courses WHERE id IN ({placeholders}){lock_clause}",
            course_ids,
        ).fetchall()
        courses_by_id = {c['id']: c for c in selected_courses}

        if len(courses_by_id) != len(course_ids):
            conn.execute("ROLLBACK")
            in_tx = False
            return False, "Beberapa mata kuliah yang dipilih tidak ditemukan."

        # Fetch student historical grades for Perbaikan vs MK Baru validation
        grade_rows = conn.execute(
            "SELECT course_code, grade FROM student_grades WHERE student_id = ?",
            (student_id,),
        ).fetchall()
        grades_map = {r['course_code']: r['grade'] for r in grade_rows}

        for course in selected_courses:
            if course['status'] in ('Dibatalkan', 'Menunggu Kebijakan Prodi'):
                conn.execute("ROLLBACK")
                in_tx = False
                return False, f"Mata kuliah '{course['name']}' sedang tidak dibuka untuk pendaftaran ({course['status']})."

        # 1. Total SKS Check
        total_sks = sum(course['sks'] for course in selected_courses)
        if total_sks > max_sks:
            conn.execute("ROLLBACK")
            in_tx = False
            return False, (
                f"Beban studi melebihi batas maksimal {max_sks} SKS "
                f"(Anda memilih {total_sks} SKS) sesuai SK Rektor No. 686/2025."
            )

        # 2. Validation per course: Perbaikan Nilai vs Mata Kuliah Baru
        resolved_items: list[dict] = []
        student_ipk = float(student['ipk'] or 0.0)
        for item in normalized_items:
            course = courses_by_id[item['course_id']]
            hist_grade = grades_map.get(course['code'])
            jenis = item['jenis_pengambilan']

            if not jenis:
                jenis = 'Perbaikan Nilai' if hist_grade in ELIGIBLE_IMPROVEMENT_GRADES else 'Mata Kuliah Baru'

            if jenis == 'Perbaikan Nilai':
                if not hist_grade:
                    conn.execute("ROLLBACK")
                    in_tx = False
                    return False, (
                        f"Mata kuliah '{course['name']}' belum memiliki riwayat nilai sebelumnya. "
                        "Pilih opsi 'Mata Kuliah Baru' jika ingin mengambil untuk percepatan studi."
                    )
                if hist_grade not in ELIGIBLE_IMPROVEMENT_GRADES:
                    conn.execute("ROLLBACK")
                    in_tx = False
                    return False, (
                        f"Perbaikan nilai untuk '{course['name']}' ditolak (Auto-Check 1): "
                        f"Nilai historis Anda adalah {hist_grade}. Perbaikan hanya diperbolehkan bagi nilai C+, C, C-, D, atau E."
                    )
                nilai_lama = hist_grade
            else:
                jenis = 'Mata Kuliah Baru'
                if hist_grade and hist_grade not in ELIGIBLE_IMPROVEMENT_GRADES:
                    conn.execute("ROLLBACK")
                    in_tx = False
                    return False, (
                        f"Mata kuliah '{course['name']}' sudah pernah Anda tempuh dengan nilai {hist_grade}."
                    )
                if student_ipk < 3.00:
                    conn.execute("ROLLBACK")
                    in_tx = False
                    return False, (
                        f"Pengambilan Mata Kuliah Baru '{course['name']}' ditolak (Auto-Check 1): "
                        f"Syarat akselerasi studi membutuhkan IPK minimal 3,00 (IPK Anda saat ini: {student_ipk:.2f})."
                    )
                nilai_lama = None

            resolved_items.append({
                'course_id': course['id'],
                'jenis_pengambilan': jenis,
                'nilai_lama': nilai_lama,
            })

        # 3. Schedule Conflict Check
        time_slots: dict[str, str] = {}
        for course in selected_courses:
            slot_key = f"{course['schedule_day']}_{course['schedule_time']}"
            if slot_key in time_slots:
                conn.execute("ROLLBACK")
                in_tx = False
                conflict_course = time_slots[slot_key]
                return False, (
                    f"Terdapat bentrok jadwal antara mata kuliah '{course['name']}' "
                    f"dan '{conflict_course}' pada {course['schedule_day']}, {course['schedule_time']}."
                )
            time_slots[slot_key] = course['name']

        # 4. NFR-03 / Auto-Check 2: Real-time Quota Availability Check
        for course in selected_courses:
            enrolled_row = conn.execute(
                '''
                SELECT COUNT(*) AS current_enrolled
                FROM krs_items ki
                JOIN krs_applications ka ON ki.application_id = ka.id
                WHERE ki.course_id = ? AND ki.status = 'Aktif'
                  AND ka.status NOT IN ('Dibatalkan', 'Expired')
                  AND ka.student_id != ?
                ''',
                (course['id'], student_id),
            ).fetchone()
            current_enrolled = enrolled_row['current_enrolled'] if enrolled_row else 0

            if current_enrolled >= course['quota']:
                conn.execute("ROLLBACK")
                in_tx = False
                return False, (
                    f"Kuota kelas untuk mata kuliah '{course['name']}' sudah penuh "
                    f"({current_enrolled}/{course['quota']}). Silakan pilih kelas paralel lain."
                )

        # 5. Create or Update Application (including revision before registration close FR-06)
        if existing_app:
            app_id = existing_app['id']
            conn.execute("DELETE FROM krs_items WHERE application_id = ?", (app_id,))
            conn.execute(
                "DELETE FROM invoices WHERE application_id = ? AND status = 'Belum Lunas'",
                (app_id,),
            )
            conn.execute(
                '''
                UPDATE krs_applications
                SET total_sks = ?,
                    status = 'Diajukan',
                    status_final = 'Diajukan',
                    dpa_notes = NULL,
                    dpa_verified_by = NULL,
                    preferred_bank = ?,
                    submitted_at = CURRENT_TIMESTAMP,
                    verified_at = NULL
                WHERE id = ?
                ''',
                (total_sks, chosen_bank, app_id),
            )
        else:
            app_id = conn.insert_returning_id(
                '''
                INSERT INTO krs_applications (
                    student_id, semester_period, total_sks, status, status_final, preferred_bank
                )
                VALUES (?, ?, ?, 'Diajukan', 'Diajukan', ?)
                ''',
                (student_id, active_semester, total_sks, chosen_bank),
            )

        for item in resolved_items:
            conn.execute(
                '''
                INSERT INTO krs_items (application_id, course_id, status, jenis_pengambilan, nilai_lama)
                VALUES (?, ?, 'Aktif', ?, ?)
                ''',
                (app_id, item['course_id'], item['jenis_pengambilan'], item['nilai_lama']),
            )

        conn.execute("COMMIT")
        in_tx = False
        return True, (
            "Kartu Rencana Studi (KRS) berhasil dikirim dan menunggu verifikasi Dosen Pembimbing Akademik (DPA)."
        )
    except Exception as exc:
        if in_tx:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
        return False, f"Terjadi kesalahan saat menyimpan KRS: {str(exc)}"
    finally:
        conn.close()


def cancel_student_krs(student_id: int) -> tuple[bool, str]:
    """FR-06: Fasilitas bagi mahasiswa untuk membatalkan pengajuan KRS sebelum masa pendaftaran ditutup."""
    if get_config('registration_status', 'Buka') != 'Buka':
        return False, "Pembatalan KRS tidak dapat dilakukan karena periode pendaftaran sudah ditutup."

    active_semester = get_config('active_semester', 'Semester Antara 2026/2027')
    conn = get_db()
    try:
        app_row = conn.execute(
            "SELECT * FROM krs_applications WHERE student_id = ? AND semester_period = ?",
            (student_id, active_semester),
        ).fetchone()
        if not app_row:
            return False, "Anda belum memiliki pengajuan KRS untuk dibatalkan."
        if app_row['status'] == 'Lunas':
            return False, "Pengajuan yang sudah Lunas tidak dapat dibatalkan."

        conn.execute(
            "UPDATE krs_items SET status = 'Dibatalkan Mahasiswa' WHERE application_id = ?",
            (app_row['id'],),
        )
        conn.execute(
            "DELETE FROM invoices WHERE application_id = ? AND status = 'Belum Lunas'",
            (app_row['id'],),
        )
        conn.execute(
            '''
            UPDATE krs_applications
            SET total_sks = 0,
                status = 'Dibatalkan',
                status_final = 'Dibatalkan',
                dpa_notes = 'Dibatalkan oleh mahasiswa sebelum penutupan pendaftaran (FR-06).'
            WHERE id = ?
            ''',
            (app_row['id'],),
        )
        conn.commit()
        return True, "Pengajuan KRS Anda berhasil dibatalkan dan kuota kelas telah dilepas (FR-06)."
    finally:
        conn.close()


def get_student_application(student_id: int):
    active_semester = get_config('active_semester', 'Semester Antara 2026/2027')
    conn = get_db()
    try:
        app_row = conn.execute(
            '''
            SELECT ka.*,
                   u.name AS student_name,
                   u.nim_nip,
                   u.prodi,
                   u.ipk,
                   u.semester,
                   u.status_sanksi,
                   dpa.name AS dpa_name,
                   dpa.nim_nip AS dpa_nip
            FROM krs_applications ka
            JOIN users u ON ka.student_id = u.id
            LEFT JOIN users dpa ON u.dpa_id = dpa.id
            WHERE ka.student_id = ? AND ka.semester_period = ?
            ''',
            (student_id, active_semester),
        ).fetchone()

        items = []
        invoice = None
        if app_row:
            items = conn.execute(
                '''
                SELECT ki.*,
                       c.code, c.name, c.sks, c.schedule_day, c.schedule_time,
                       c.room, c.lecturer_name, c.status AS course_status, c.prodi_name
                FROM krs_items ki
                JOIN courses c ON ki.course_id = c.id
                WHERE ki.application_id = ?
                ORDER BY ki.id ASC
                ''',
                (app_row['id'],),
            ).fetchall()

            invoice = conn.execute(
                "SELECT * FROM invoices WHERE application_id = ?",
                (app_row['id'],),
            ).fetchone()

        return app_row, items, invoice
    finally:
        conn.close()


def get_dpa_applications(dpa_id: int | None = None):
    """UC-DPA-02 & FR-08: Return KRS applications of mentees assigned to this DPA (or all for Super Admin)."""
    active_semester = get_config('active_semester', 'Semester Antara 2026/2027')
    conn = get_db()
    try:
        if dpa_id is None:
            rows = conn.execute(
                '''
                SELECT ka.*, u.name AS student_name, u.nim_nip, u.prodi, u.ipk, u.semester,
                       u.status_sanksi, dpa.name AS dpa_name
                FROM krs_applications ka
                JOIN users u ON ka.student_id = u.id
                LEFT JOIN users dpa ON u.dpa_id = dpa.id
                WHERE ka.semester_period = ? AND ka.status != 'Dibatalkan'
                ORDER BY
                    CASE ka.status WHEN 'Diajukan' THEN 0 WHEN 'Ditolak DPA' THEN 1 WHEN 'Disetujui DPA' THEN 2 ELSE 3 END,
                    ka.submitted_at DESC, ka.id DESC
                ''',
                (active_semester,),
            ).fetchall()
        else:
            rows = conn.execute(
                '''
                SELECT ka.*, u.name AS student_name, u.nim_nip, u.prodi, u.ipk, u.semester,
                       u.status_sanksi, dpa.name AS dpa_name
                FROM krs_applications ka
                JOIN users u ON ka.student_id = u.id
                LEFT JOIN users dpa ON u.dpa_id = dpa.id
                WHERE u.dpa_id = ? AND ka.semester_period = ? AND ka.status != 'Dibatalkan'
                ORDER BY
                    CASE ka.status WHEN 'Diajukan' THEN 0 WHEN 'Ditolak DPA' THEN 1 WHEN 'Disetujui DPA' THEN 2 ELSE 3 END,
                    ka.submitted_at DESC, ka.id DESC
                ''',
                (dpa_id, active_semester),
            ).fetchall()

        result = []
        for row in rows:
            app_dict = dict(row)
            items = conn.execute(
                '''
                SELECT ki.id, ki.status, ki.jenis_pengambilan, ki.nilai_lama,
                       c.code, c.name, c.sks, c.schedule_day, c.schedule_time, c.status AS course_status
                FROM krs_items ki
                JOIN courses c ON ki.course_id = c.id
                WHERE ki.application_id = ?
                ORDER BY c.code ASC
                ''',
                (row['id'],),
            ).fetchall()
            app_dict['krs_items'] = [dict(i) for i in items]
            result.append(app_dict)
        return result
    finally:
        conn.close()


def approve_student_krs(
    application_id: int,
    dpa_id: int | None = None,
    notes: str = '',
    allow_any: bool = False,
) -> tuple[bool, str]:
    """
    UC-DPA-02, SD-02, AD-02, & BR-08:
    DPA menyetujui pengajuan mahasiswa bimbingannya.
    Sesuai BR-08, tagihan VA HANYA diterbitkan jika pendaftaran sudah ditutup
    DAN seluruh kelas yang diambil sudah resmi Dibuka / Dispensasi Buka oleh Prodi.
    """
    conn = get_db()
    try:
        app_row = conn.execute(
            '''
            SELECT ka.*, u.dpa_id, u.name AS student_name
            FROM krs_applications ka
            JOIN users u ON ka.student_id = u.id
            WHERE ka.id = ?
            ''',
            (application_id,),
        ).fetchone()
        if not app_row:
            return False, f"Pengajuan KRS #{application_id} tidak ditemukan."

        if not allow_any and dpa_id is not None and app_row['dpa_id'] != dpa_id:
            return False, "Akses ditolak: Mahasiswa tersebut bukan mahasiswa bimbingan akademik Anda."

        clean_notes = (notes or '').strip() or 'Disetujui oleh Dosen Pembimbing Akademik (DPA).'
        conn.execute(
            '''
            UPDATE krs_applications
            SET status = 'Disetujui DPA',
                status_final = 'Menunggu Kepastian Kelas Buka',
                dpa_notes = ?,
                dpa_verified_by = ?,
                verified_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''',
            (clean_notes, dpa_id, application_id),
        )

        va_issued, _ = issue_invoice_if_eligible_in_tx(conn, application_id)
        conn.commit()
        if va_issued:
            return True, (
                f"Pengajuan KRS #{application_id} ({app_row['student_name']}) berhasil DISETUJUI DPA "
                "dan tagihan Virtual Account telah diterbitkan."
            )
        return True, (
            f"Pengajuan KRS #{application_id} ({app_row['student_name']}) berhasil DISETUJUI DPA. "
            "Sesuai BR-08, tagihan VA akan terbit otomatis setelah pendaftaran ditutup dan kelas resmi dibuka Prodi."
        )
    finally:
        conn.close()


def reject_student_krs(
    application_id: int,
    notes: str,
    dpa_id: int | None = None,
    allow_any: bool = False,
) -> tuple[bool, str]:
    """UC-DPA-02 & BR-04: DPA menolak pengajuan agar mahasiswa berkonsultasi & revisi."""
    conn = get_db()
    try:
        app_row = conn.execute(
            '''
            SELECT ka.*, u.dpa_id, u.name AS student_name
            FROM krs_applications ka
            JOIN users u ON ka.student_id = u.id
            WHERE ka.id = ?
            ''',
            (application_id,),
        ).fetchone()
        if not app_row:
            return False, f"Pengajuan KRS #{application_id} tidak ditemukan."

        if not allow_any and dpa_id is not None and app_row['dpa_id'] != dpa_id:
            return False, "Akses ditolak: Mahasiswa tersebut bukan mahasiswa bimbingan akademik Anda."

        clean_notes = (notes or '').strip() or 'Silakan berkonsultasi dan revisi pilihan mata kuliah dengan DPA.'
        conn.execute(
            '''
            UPDATE krs_applications
            SET status = 'Ditolak DPA',
                status_final = 'Ditolak Pembimbing',
                dpa_notes = ?,
                dpa_verified_by = ?,
                verified_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''',
            (clean_notes, dpa_id, application_id),
        )
        conn.commit()
        return True, (
            f"Pengajuan KRS #{application_id} ({app_row['student_name']}) DITOLAK DPA dengan catatan: '{clean_notes}'."
        )
    finally:
        conn.close()


def get_lecturer_official_roster(lecturer_id: int | None = None):
    """
    FR-12: Menampilkan jadwal mengajar definitif dan daftar peserta resmi
    yang telah melunasi tagihan Virtual Account untuk mata kuliah yang diampu dosen.
    """
    active_semester = get_config('active_semester', 'Semester Antara 2026/2027')
    conn = get_db()
    try:
        filter_clause = ""
        params: list = [active_semester]
        if lecturer_id is not None:
            filter_clause = "AND c.lecturer_id = ?"
            params.append(lecturer_id)

        return conn.execute(
            f'''
            SELECT c.id AS course_id, c.code AS course_code, c.name AS course_name, c.sks,
                   c.schedule_day, c.schedule_time, c.room, c.status AS class_status,
                   u.nim_nip, u.name AS student_name, u.prodi, u.semester,
                   ki.jenis_pengambilan,
                   inv.va_number, inv.bank_name, inv.paid_at
            FROM krs_items ki
            JOIN courses c ON ki.course_id = c.id
            JOIN krs_applications ka ON ki.application_id = ka.id
            JOIN users u ON ka.student_id = u.id
            JOIN invoices inv ON ka.id = inv.application_id
            WHERE ka.semester_period = ?
              AND ka.status = 'Lunas'
              AND ki.status = 'Aktif'
              AND c.status IN ('Dibuka', 'Dispensasi Buka')
              {filter_clause}
            ORDER BY c.code ASC, u.nim_nip ASC
            ''',
            tuple(params),
        ).fetchall()
    finally:
        conn.close()
