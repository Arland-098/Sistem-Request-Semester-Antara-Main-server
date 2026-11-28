from database import DB_INTEGRITY_ERRORS, get_db
from services.billing_service import (
    _get_student_rate_in_tx,
    issue_invoice_if_eligible_in_tx,
    sync_invoices_for_ready_applications,
)
from services.config_service import get_config, set_config


def get_courses_list(prodi_code: str | None = None):
    conn = get_db()
    try:
        filter_clause = ""
        params: tuple = ()
        if prodi_code and prodi_code != 'ALL':
            filter_clause = "WHERE c.prodi_code = ?"
            params = (prodi_code,)

        return conn.execute(
            f'''
            SELECT c.*,
                   COUNT(
                       CASE
                           WHEN ki.status = 'Aktif' AND ka.status NOT IN ('Dibatalkan', 'Expired')
                           THEN ki.id
                       END
                   ) AS enrolled_count,
                   COUNT(
                       CASE
                           WHEN ki.status = 'Aktif' AND ka.status IN ('Disetujui DPA', 'Lunas')
                           THEN ki.id
                       END
                   ) AS approved_count
            FROM courses c
            LEFT JOIN krs_items ki ON c.id = ki.course_id
            LEFT JOIN krs_applications ka ON ki.application_id = ka.id
            {filter_clause}
            GROUP BY c.id
            ORDER BY c.semester ASC, c.code ASC
            ''',
            params,
        ).fetchall()
    finally:
        conn.close()


def get_courses_grouped_by_semester(prodi_code: str | None = None):
    courses = get_courses_list(prodi_code=prodi_code)
    grouped = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    for course in courses:
        sem = course['semester'] if course['semester'] in grouped else 1
        grouped[sem].append(course)
    return grouped


def get_course_by_id(course_id: int):
    conn = get_db()
    try:
        return conn.execute(
            '''
            SELECT c.*,
                   COUNT(
                       CASE
                           WHEN ki.status = 'Aktif' AND ka.status NOT IN ('Dibatalkan', 'Expired')
                           THEN ki.id
                       END
                   ) AS enrolled_count,
                   COUNT(
                       CASE
                           WHEN ki.status = 'Aktif' AND ka.status IN ('Disetujui DPA', 'Lunas')
                           THEN ki.id
                       END
                   ) AS approved_count
            FROM courses c
            LEFT JOIN krs_items ki ON c.id = ki.course_id
            LEFT JOIN krs_applications ka ON ki.application_id = ka.id
            WHERE c.id = ?
            GROUP BY c.id
            ''',
            (course_id,),
        ).fetchone()
    finally:
        conn.close()


def add_course(
    code: str,
    name: str,
    sks: int,
    day: str,
    time_str: str,
    room: str,
    quota: int,
    lecturer_id: int | None,
    semester: int = 1,
    class_name: str = '1ATI',
    wp_type: str = 'W',
    prodi_code: str = '60',
) -> tuple[bool, str]:
    normalized_code = (code or '').strip().upper()
    normalized_name = (name or '').strip()
    if not normalized_code or not normalized_name:
        return False, "Kode dan nama mata kuliah wajib diisi."

    conn = get_db()
    try:
        lecturer_name = ''
        if lecturer_id:
            lecturer = conn.execute(
                "SELECT name FROM users WHERE id = ?",
                (lecturer_id,),
            ).fetchone()
            lecturer_name = lecturer['name'] if lecturer else ''

        clean_prodi_code = (prodi_code or '60').strip()
        prog = conn.execute(
            "SELECT name FROM programs WHERE code = ?",
            (clean_prodi_code,),
        ).fetchone()
        prodi_name = prog['name'] if prog else 'Teknik Informatika'

        min_quota = int(get_config('min_quota', '10') or 10)
        conn.execute(
            '''
            INSERT INTO courses (
                code, name, sks, schedule_day, schedule_time, room, quota, min_quota,
                lecturer_id, lecturer_name, prodi_code, prodi_name,
                status, semester, class_name, wp_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Menunggu', ?, ?, ?)
            ''',
            (
                normalized_code,
                normalized_name,
                sks,
                day,
                time_str,
                room,
                quota,
                min_quota,
                lecturer_id,
                lecturer_name,
                clean_prodi_code,
                prodi_name,
                semester,
                class_name or f'{semester}ATI',
                wp_type if wp_type in ('W', 'P') else 'W',
            ),
        )
        conn.commit()
        return True, f"Mata kuliah {normalized_code} - {normalized_name} berhasil ditambahkan ke katalog resmi."
    except DB_INTEGRITY_ERRORS:
        conn.rollback()
        return False, f"Kode mata kuliah '{normalized_code}' sudah terdaftar di katalog."
    finally:
        conn.close()


def update_course_details(
    course_id: int,
    name: str,
    sks: int,
    day: str,
    time_str: str,
    room: str,
    quota: int,
    lecturer_id: int | None,
    semester: int | None = None,
    class_name: str | None = None,
    wp_type: str | None = None,
    prodi_code: str | None = None,
) -> tuple[bool, str]:
    conn = get_db()
    try:
        existing = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
        if not existing:
            return False, f"Mata kuliah #{course_id} tidak ditemukan."

        if lecturer_id:
            lecturer = conn.execute(
                "SELECT name FROM users WHERE id = ?",
                (lecturer_id,),
            ).fetchone()
            lecturer_name = lecturer['name'] if lecturer else existing['lecturer_name']
        else:
            lecturer_id = existing['lecturer_id']
            lecturer_name = existing['lecturer_name']

        next_prodi_code = (prodi_code or '').strip() or existing['prodi_code']
        prog = conn.execute(
            "SELECT name FROM programs WHERE code = ?",
            (next_prodi_code,),
        ).fetchone()
        next_prodi_name = prog['name'] if prog else existing['prodi_name']

        next_semester = semester if semester is not None else existing['semester']
        next_class = class_name if class_name else existing['class_name']
        next_wp = wp_type if wp_type in ('W', 'P') else existing['wp_type']

        conn.execute(
            '''
            UPDATE courses
            SET name = ?, sks = ?, schedule_day = ?, schedule_time = ?, room = ?,
                quota = ?, lecturer_id = ?, lecturer_name = ?,
                prodi_code = ?, prodi_name = ?,
                semester = ?, class_name = ?, wp_type = ?
            WHERE id = ?
            ''',
            (
                (name or '').strip() or existing['name'],
                sks,
                day,
                time_str,
                room,
                quota,
                lecturer_id,
                lecturer_name,
                next_prodi_code,
                next_prodi_name,
                next_semester,
                next_class,
                next_wp,
                course_id,
            ),
        )
        conn.commit()
        return True, f"Data mata kuliah #{course_id} berhasil diperbarui."
    finally:
        conn.close()


def update_course_schedule(course_id: int, day: str, time_str: str, room: str) -> None:
    conn = get_db()
    try:
        conn.execute(
            '''
            UPDATE courses
            SET schedule_day = ?, schedule_time = ?, room = ?
            WHERE id = ?
            ''',
            (day, time_str, room, course_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_course(course_id: int) -> tuple[bool, str]:
    conn = get_db()
    try:
        conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        conn.commit()
        return True, f"Mata kuliah #{course_id} telah dihapus dari katalog."
    except DB_INTEGRITY_ERRORS:
        conn.rollback()
        return False, (
            f"Mata kuliah #{course_id} tidak dapat dihapus karena sudah terhubung dengan pengajuan KRS mahasiswa. "
            "Gunakan status 'Dibatalkan' pada menu Monitoring jika kelas tidak diselenggarakan."
        )
    finally:
        conn.close()


def confirm_lecturer_teaching(course_id: int, agreed: bool) -> None:
    conn = get_db()
    try:
        conn.execute(
            "UPDATE courses SET lecturer_agreed = ? WHERE id = ?",
            (1 if agreed else -1, course_id),
        )
        if agreed:
            conn.execute(
                "UPDATE courses SET status = 'Ditawarkan' WHERE id = ? AND status = 'Menunggu'",
                (course_id,),
            )
        conn.commit()
    finally:
        conn.close()


def request_class_dispensation(course_id: int) -> tuple[bool, str]:
    """SD-03 step f: Prodi requests dispensation confirmation from assigned lecturer."""
    if get_config('registration_status', 'Buka') == 'Buka':
        return False, (
            "Evaluasi kelas & permintaan dispensasi hanya dapat dilakukan setelah periode pendaftaran ditutup (UC-PRD-07)."
        )

    conn = get_db()
    try:
        course = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
        if not course:
            return False, f"Kelas #{course_id} tidak ditemukan."
        if not course['lecturer_id']:
            return False, (
                f"Kelas {course['code']} belum memiliki akun Dosen Pengampu tertaut. "
                "Tugaskan dosen pengampu di Katalog MK terlebih dahulu."
            )

        conn.execute(
            '''
            UPDATE courses
            SET dispensation_requested = 1,
                lecturer_dispensation_agreed = 0,
                status = 'Menunggu Kebijakan Prodi'
            WHERE id = ?
            ''',
            (course_id,),
        )
        conn.commit()
        return True, (
            f"Permohonan kesediaan mengajar kelas dispensasi untuk {course['code']} - {course['name']} "
            "telah dikirim ke dasbor Dosen Pengampu."
        )
    finally:
        conn.close()


def confirm_lecturer_dispensation(course_id: int, agreed: bool) -> None:
    """
    SD-03 step g: Dosen Pengampu submits readiness (Bersedia / Tidak Bersedia).
    Penetapan status final kelas ('Dispensasi Buka' / 'Dibatalkan') dilakukan oleh Program Studi di SD-03 step h.
    """
    conn = get_db()
    try:
        conn.execute(
            "UPDATE courses SET lecturer_dispensation_agreed = ?, dispensation_requested = 1 WHERE id = ?",
            (1 if agreed else -1, course_id),
        )
        conn.commit()
    finally:
        conn.close()


def close_registration_and_mark_classes() -> tuple[int, int]:
    """
    Auto-Check 3 & BR-05:
    Kunci pendaftaran dan evaluasi kelas yang masih Ditawarkan/Menunggu:
    - Pendaftar Disetujui DPA < min_quota -> tandai 'Menunggu Kebijakan Prodi'
    - Pendaftar >= min_quota -> siap ditetapkan Prodi menjadi 'Dibuka'.
    """
    set_config('registration_status', 'Tutup')
    min_quota = int(get_config('min_quota', '10') or 10)
    courses = get_courses_list()

    conn = get_db()
    under_quota_count = 0
    ready_quota_count = 0
    try:
        for course in courses:
            if course['status'] in ('Ditawarkan', 'Menunggu'):
                if course['approved_count'] < min_quota:
                    conn.execute(
                        "UPDATE courses SET status = 'Menunggu Kebijakan Prodi' WHERE id = ?",
                        (course['id'],),
                    )
                    under_quota_count += 1
                else:
                    ready_quota_count += 1
        conn.commit()
    finally:
        conn.close()

    sync_invoices_for_ready_applications()
    return ready_quota_count, under_quota_count


def _recalculate_application_after_cancel_in_tx(conn, app_id: int) -> None:
    app_row = conn.execute(
        "SELECT * FROM krs_applications WHERE id = ?",
        (app_id,),
    ).fetchone()
    if not app_row:
        return

    row = conn.execute(
        '''
        SELECT COALESCE(SUM(c.sks), 0) AS total
        FROM krs_items ki
        JOIN courses c ON ki.course_id = c.id
        WHERE ki.application_id = ? AND ki.status = 'Aktif'
        ''',
        (app_id,),
    ).fetchone()
    total_sks = row['total'] if row else 0

    if total_sks <= 0:
        conn.execute(
            "UPDATE krs_applications SET total_sks = 0, status = 'Dibatalkan', status_final = 'Dibatalkan' WHERE id = ?",
            (app_id,),
        )
        conn.execute(
            "DELETE FROM invoices WHERE application_id = ? AND status = 'Belum Lunas'",
            (app_id,),
        )
        return

    conn.execute(
        "UPDATE krs_applications SET total_sks = ? WHERE id = ?",
        (total_sks, app_id),
    )

    cfg = {
        r['key']: r['value']
        for r in conn.execute("SELECT key, value FROM system_config").fetchall()
    }
    sks_rate = _get_student_rate_in_tx(conn, app_row['student_id'], cfg)
    conn.execute(
        "UPDATE invoices SET amount = ? WHERE application_id = ? AND status = 'Belum Lunas'",
        (total_sks * sks_rate, app_id),
    )

    if app_row['status'] == 'Disetujui DPA':
        issue_invoice_if_eligible_in_tx(conn, app_id)


def update_course_status(course_id: int, new_status: str) -> tuple[bool, str]:
    """
    UC-PRD-07 & AD-03 & BR-07 & BR-08:
    Program Studi menetapkan status definitif kelas setelah pendaftaran ditutup.
    """
    course = get_course_by_id(course_id)
    if not course:
        return False, f"Kelas #{course_id} tidak ditemukan."

    reg_status = get_config('registration_status', 'Buka')
    min_quota = int(get_config('min_quota', '10') or 10)

    if new_status in ('Dibuka', 'Dispensasi Buka') and reg_status == 'Buka':
        return False, (
            "Fungsi penetapan kelas dinonaktifkan sebelum periode pendaftaran ditutup (UC-PRD-07 Eksepsi 1a). "
            "Silakan tutup periode pendaftaran terlebih dahulu."
        )

    if new_status == 'Dibuka' and course['approved_count'] < min_quota:
        return False, (
            f"Kelas {course['code']} hanya memiliki {course['approved_count']} pendaftar disetujui DPA "
            f"(syarat minimal {min_quota} mahasiswa sesuai BR-05). Ajukan dispensasi ke Dosen Pengampu atau batalkan kelas."
        )

    if new_status == 'Dispensasi Buka' and course['lecturer_dispensation_agreed'] != 1:
        return False, (
            f"Dosen Pengampu untuk {course['code']} belum mengonfirmasi 'Bersedia' mengajar kelas dispensasi (SD-03)."
        )

    conn = get_db()
    try:
        conn.execute(
            "UPDATE courses SET status = ? WHERE id = ?",
            (new_status, course_id),
        )

        if new_status == 'Dibatalkan':
            conn.execute(
                "UPDATE krs_items SET status = 'Dibatalkan Prodi' WHERE course_id = ? AND status = 'Aktif'",
                (course_id,),
            )
            affected_apps = conn.execute(
                "SELECT DISTINCT application_id FROM krs_items WHERE course_id = ?",
                (course_id,),
            ).fetchall()
            for app in affected_apps:
                _recalculate_application_after_cancel_in_tx(conn, app['application_id'])

        conn.commit()
    finally:
        conn.close()

    issued = 0
    if new_status in ('Dibuka', 'Dispensasi Buka', 'Dibatalkan'):
        issued = sync_invoices_for_ready_applications()

    extra = f" ({issued} tagihan Virtual Account mahasiswa diterbitkan otomatis sesuai BR-08.)" if issued else ""
    return True, f"Status kelas {course['code']} berhasil ditetapkan menjadi: {new_status}.{extra}"
