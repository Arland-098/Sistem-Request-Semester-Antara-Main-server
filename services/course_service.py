from database import DB_INTEGRITY_ERRORS, get_db


def get_courses_list():
    conn = get_db()
    try:
        return conn.execute('''
        SELECT c.*,
               COUNT(CASE WHEN ki.status = 'Aktif' THEN ki.id END) AS enrolled_count
        FROM courses c
        LEFT JOIN krs_items ki ON c.id = ki.course_id
        GROUP BY c.id
        ORDER BY c.semester ASC, c.code ASC
        ''').fetchall()
    finally:
        conn.close()


def get_courses_grouped_by_semester():
    courses = get_courses_list()
    grouped = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    for course in courses:
        sem = course['semester'] if course['semester'] in grouped else 1
        grouped[sem].append(course)
    return grouped


def get_course_by_id(course_id: int):
    conn = get_db()
    try:
        return conn.execute('''
        SELECT c.*,
               COUNT(CASE WHEN ki.status = 'Aktif' THEN ki.id END) AS enrolled_count
        FROM courses c
        LEFT JOIN krs_items ki ON c.id = ki.course_id
        WHERE c.id = ?
        GROUP BY c.id
        ''', (course_id,)).fetchone()
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

        conn.execute('''
        INSERT INTO courses (
            code, name, sks, schedule_day, schedule_time, room, quota,
            lecturer_id, lecturer_name, status, semester, class_name, wp_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Menunggu', ?, ?, ?)
        ''', (
            normalized_code,
            normalized_name,
            sks,
            day,
            time_str,
            room,
            quota,
            lecturer_id,
            lecturer_name,
            semester,
            class_name or f'{semester}ATI',
            wp_type if wp_type in ('W', 'P') else 'W',
        ))
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

        next_semester = semester if semester is not None else existing['semester']
        next_class = class_name if class_name else existing['class_name']
        next_wp = wp_type if wp_type in ('W', 'P') else existing['wp_type']

        conn.execute('''
        UPDATE courses
        SET name = ?, sks = ?, schedule_day = ?, schedule_time = ?, room = ?,
            quota = ?, lecturer_id = ?, lecturer_name = ?,
            semester = ?, class_name = ?, wp_type = ?
        WHERE id = ?
        ''', (
            (name or '').strip() or existing['name'],
            sks,
            day,
            time_str,
            room,
            quota,
            lecturer_id,
            lecturer_name,
            next_semester,
            next_class,
            next_wp,
            course_id,
        ))
        conn.commit()
        return True, f"Data mata kuliah #{course_id} berhasil diperbarui."
    finally:
        conn.close()


def update_course_schedule(course_id: int, day: str, time_str: str, room: str) -> None:
    conn = get_db()
    try:
        conn.execute('''
        UPDATE courses
        SET schedule_day = ?, schedule_time = ?, room = ?
        WHERE id = ?
        ''', (day, time_str, room, course_id))
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
                "UPDATE courses SET status = 'Dibuka' WHERE id = ? AND status = 'Menunggu'",
                (course_id,),
            )
        conn.commit()
    finally:
        conn.close()


def confirm_lecturer_dispensation(course_id: int, agreed: bool) -> None:
    conn = get_db()
    try:
        conn.execute(
            "UPDATE courses SET lecturer_dispensation_agreed = ? WHERE id = ?",
            (1 if agreed else -1, course_id),
        )
        if agreed:
            conn.execute(
                "UPDATE courses SET status = 'Dispensasi Buka' WHERE id = ?",
                (course_id,),
            )
        else:
            conn.execute(
                "UPDATE courses SET status = 'Dibatalkan' WHERE id = ?",
                (course_id,),
            )
        conn.commit()
    finally:
        conn.close()


def _recalculate_application_sks_in_tx(conn, app_id: int) -> None:
    row = conn.execute('''
    SELECT COALESCE(SUM(c.sks), 0) AS total
    FROM krs_items ki
    JOIN courses c ON ki.course_id = c.id
    WHERE ki.application_id = ? AND ki.status = 'Aktif'
    ''', (app_id,)).fetchone()
    total_sks = row['total'] if row else 0
    conn.execute(
        "UPDATE krs_applications SET total_sks = ? WHERE id = ?",
        (total_sks, app_id),
    )

    rate_row = conn.execute(
        "SELECT value FROM system_config WHERE key = 'sks_rate'"
    ).fetchone()
    sks_rate = int(rate_row['value']) if rate_row else 220000
    conn.execute(
        "UPDATE invoices SET amount = ? WHERE application_id = ? AND status = 'Belum Lunas'",
        (total_sks * sks_rate, app_id),
    )


def update_course_status(course_id: int, new_status: str) -> None:
    conn = get_db()
    try:
        conn.execute(
            "UPDATE courses SET status = ? WHERE id = ?",
            (new_status, course_id),
        )

        if new_status == 'Dibatalkan':
            conn.execute(
                "UPDATE krs_items SET status = 'Dibatalkan' WHERE course_id = ?",
                (course_id,),
            )
            affected_apps = conn.execute(
                "SELECT DISTINCT application_id FROM krs_items WHERE course_id = ?",
                (course_id,),
            ).fetchall()
            for app in affected_apps:
                _recalculate_application_sks_in_tx(conn, app['application_id'])

        conn.commit()
    finally:
        conn.close()
