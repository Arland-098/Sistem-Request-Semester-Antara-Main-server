import random
from database import get_db
from services.config_service import get_config


def submit_student_krs(student_id: int, course_ids: list[int]) -> tuple[bool, str]:
    """
    Submit KRS dengan validasi akademik dan transaksi locking atomik (NFR-03):
    - Periode pendaftaran harus terbuka (FR-14)
    - Batas maksimal beban SKS sesuai SK Rektor 686/2025 (default 9 SKS)
    - Anti-bentrok jadwal kuliah luring
    - Pemeriksaan kuota real-time dengan penguncian transaksi (BEGIN EXCLUSIVE / FOR UPDATE)
    """
    unique_course_ids = list(dict.fromkeys(course_ids))
    if not unique_course_ids:
        return False, "Pilih minimal 1 mata kuliah."

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
            return False, "Periode pendaftaran Semester Antara sedang ditutup."

        active_semester = cfg.get('active_semester', 'Semester Antara 2026/2027')
        max_sks = int(cfg.get('max_sks', '9'))

        existing_app = conn.execute('''
        SELECT id, status FROM krs_applications
        WHERE student_id = ? AND semester_period = ?
        ''', (student_id, active_semester)).fetchone()

        if existing_app and existing_app['status'] not in ('Draft', 'Ditolak DPA'):
            conn.execute("ROLLBACK")
            in_tx = False
            return False, (
                f"Pengajuan KRS Anda saat ini berstatus '{existing_app['status']}' "
                "dan tidak dapat diubah."
            )

        placeholders = ','.join('?' for _ in unique_course_ids)
        lock_clause = " FOR UPDATE" if conn.is_postgres else ""
        selected_courses = conn.execute(
            f"SELECT * FROM courses WHERE id IN ({placeholders}){lock_clause}",
            unique_course_ids,
        ).fetchall()

        if len(selected_courses) != len(unique_course_ids):
            conn.execute("ROLLBACK")
            in_tx = False
            return False, "Beberapa mata kuliah yang dipilih tidak ditemukan."

        for course in selected_courses:
            if course['status'] == 'Dibatalkan':
                conn.execute("ROLLBACK")
                in_tx = False
                return False, f"Mata kuliah '{course['name']}' telah dibatalkan oleh Program Studi."

        # 1. Total SKS Check
        total_sks = sum(course['sks'] for course in selected_courses)
        if total_sks > max_sks:
            conn.execute("ROLLBACK")
            in_tx = False
            return False, (
                f"Beban studi melebihi batas maksimal {max_sks} SKS "
                f"(Anda memilih {total_sks} SKS) sesuai SK Rektor No. 686/2025."
            )

        # 2. Schedule Conflict Check
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

        # 3. NFR-03: Real-time Quota Availability Check
        for course in selected_courses:
            enrolled_row = conn.execute('''
            SELECT COUNT(*) AS current_enrolled
            FROM krs_items ki
            JOIN krs_applications ka ON ki.application_id = ka.id
            WHERE ki.course_id = ? AND ki.status = 'Aktif' AND ka.student_id != ?
            ''', (course['id'], student_id)).fetchone()
            current_enrolled = enrolled_row['current_enrolled'] if enrolled_row else 0

            if current_enrolled >= course['quota']:
                conn.execute("ROLLBACK")
                in_tx = False
                return False, (
                    f"Kuota kelas untuk mata kuliah '{course['name']}' sudah penuh "
                    f"({current_enrolled}/{course['quota']}). Pendaftaran dibatalkan."
                )

        # 4. Create or Update Application
        if existing_app:
            app_id = existing_app['id']
            conn.execute("DELETE FROM krs_items WHERE application_id = ?", (app_id,))
            conn.execute('''
            UPDATE krs_applications
            SET total_sks = ?, status = 'Diajukan', dpa_notes = NULL, submitted_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (total_sks, app_id))
        else:
            app_id = conn.insert_returning_id(
                '''
                INSERT INTO krs_applications (student_id, semester_period, total_sks, status)
                VALUES (?, ?, ?, 'Diajukan')
                ''',
                (student_id, active_semester, total_sks),
            )

        for cid in unique_course_ids:
            conn.execute('''
            INSERT INTO krs_items (application_id, course_id, status)
            VALUES (?, ?, 'Aktif')
            ''', (app_id, cid))

        conn.execute("COMMIT")
        in_tx = False
        return True, (
            "Kartu Rencana Studi (KRS) berhasil diajukan dan sedang menunggu "
            "verifikasi Dosen Pembimbing Akademik."
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


def get_student_application(student_id: int):
    active_semester = get_config('active_semester', 'Semester Antara 2026/2027')
    conn = get_db()
    try:
        app_row = conn.execute('''
        SELECT ka.*, u.name AS student_name, u.nim_nip, u.prodi, u.ipk, dpa.name AS dpa_name
        FROM krs_applications ka
        JOIN users u ON ka.student_id = u.id
        LEFT JOIN users dpa ON u.dpa_id = dpa.id
        WHERE ka.student_id = ? AND ka.semester_period = ?
        ''', (student_id, active_semester)).fetchone()

        items = []
        invoice = None
        if app_row:
            items = conn.execute('''
            SELECT ki.*, c.code, c.name, c.sks, c.schedule_day, c.schedule_time,
                   c.room, c.lecturer_name, c.status AS course_status
            FROM krs_items ki
            JOIN courses c ON ki.course_id = c.id
            WHERE ki.application_id = ?
            ''', (app_row['id'],)).fetchall()

            invoice = conn.execute(
                "SELECT * FROM invoices WHERE application_id = ?",
                (app_row['id'],),
            ).fetchone()

        return app_row, items, invoice
    finally:
        conn.close()


def get_dpa_applications(dpa_id: int):
    active_semester = get_config('active_semester', 'Semester Antara 2026/2027')
    conn = get_db()
    try:
        return conn.execute('''
        SELECT ka.*, u.name AS student_name, u.nim_nip, u.prodi, u.ipk, u.semester
        FROM krs_applications ka
        JOIN users u ON ka.student_id = u.id
        WHERE u.dpa_id = ? AND ka.semester_period = ?
        ORDER BY ka.submitted_at DESC, ka.id DESC
        ''', (dpa_id, active_semester)).fetchall()
    finally:
        conn.close()


def _generate_unique_va(conn, nim: str) -> str:
    nim_suffix = (nim or '000000')[-6:].rjust(6, '0')
    for _ in range(10):
        va_number = f"8871{nim_suffix}{random.randint(100000, 999999)}"
        exists = conn.execute(
            "SELECT 1 FROM invoices WHERE va_number = ?",
            (va_number,),
        ).fetchone()
        if not exists:
            return va_number
    return f"8871{nim_suffix}{random.randint(100000, 999999)}"


def approve_student_krs(application_id: int) -> None:
    conn = get_db()
    try:
        conn.execute('''
        UPDATE krs_applications
        SET status = 'Disetujui DPA', verified_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (application_id,))

        app_row = conn.execute(
            "SELECT * FROM krs_applications WHERE id = ?",
            (application_id,),
        ).fetchone()

        if app_row:
            existing_inv = conn.execute(
                "SELECT * FROM invoices WHERE application_id = ?",
                (application_id,),
            ).fetchone()
            if not existing_inv:
                student = conn.execute(
                    "SELECT nim_nip FROM users WHERE id = ?",
                    (app_row['student_id'],),
                ).fetchone()
                nim = student['nim_nip'] if student else '000000'
                rate_row = conn.execute(
                    "SELECT value FROM system_config WHERE key = 'sks_rate'"
                ).fetchone()
                sks_rate = int(rate_row['value']) if rate_row else 220000
                amount = app_row['total_sks'] * sks_rate

                va_number = _generate_unique_va(conn, nim)
                chosen_bank = 'Bank Mandiri'

                conn.execute('''
                INSERT INTO invoices (application_id, student_id, va_number, bank_name, amount, status)
                VALUES (?, ?, ?, ?, ?, 'Belum Lunas')
                ''', (application_id, app_row['student_id'], va_number, chosen_bank, amount))

        conn.commit()
    finally:
        conn.close()


def reject_student_krs(application_id: int, notes: str) -> None:
    conn = get_db()
    try:
        conn.execute('''
        UPDATE krs_applications
        SET status = 'Ditolak DPA', dpa_notes = ?, verified_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (notes, application_id))
        conn.commit()
    finally:
        conn.close()
