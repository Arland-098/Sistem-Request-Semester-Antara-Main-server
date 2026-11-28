from werkzeug.security import generate_password_hash

from database import DB_INTEGRITY_ERRORS, get_db

VALID_ROLES = ('mahasiswa', 'dpa', 'dosen', 'prodi', 'keuangan', 'superadmin')
VALID_GRADES = ('A', 'A-', 'B+', 'B', 'C+', 'C', 'C-', 'D', 'E')


def get_user_by_id(user_id: int):
    conn = get_db()
    try:
        return conn.execute(
            '''
            SELECT u.*,
                   dpa.name AS dpa_name,
                   dpa.nim_nip AS dpa_nip,
                   COALESCE(p.rumpun_ilmu, 'Sarjana Reguler') AS rumpun_ilmu
            FROM users u
            LEFT JOIN users dpa ON u.dpa_id = dpa.id
            LEFT JOIN programs p ON u.prodi_code = p.code
            WHERE u.id = ?
            ''',
            (user_id,),
        ).fetchone()
    finally:
        conn.close()


def get_user_by_username(username: str):
    conn = get_db()
    try:
        return conn.execute(
            '''
            SELECT u.*,
                   dpa.name AS dpa_name,
                   dpa.nim_nip AS dpa_nip,
                   COALESCE(p.rumpun_ilmu, 'Sarjana Reguler') AS rumpun_ilmu
            FROM users u
            LEFT JOIN users dpa ON u.dpa_id = dpa.id
            LEFT JOIN programs p ON u.prodi_code = p.code
            WHERE u.username = ?
            ''',
            (username,),
        ).fetchone()
    finally:
        conn.close()


def get_users_by_role(role: str):
    conn = get_db()
    try:
        return conn.execute(
            '''
            SELECT u.*,
                   dpa.name AS dpa_name,
                   dpa.nim_nip AS dpa_nip,
                   COALESCE(p.rumpun_ilmu, 'Sarjana Reguler') AS rumpun_ilmu
            FROM users u
            LEFT JOIN users dpa ON u.dpa_id = dpa.id
            LEFT JOIN programs p ON u.prodi_code = p.code
            WHERE u.role = ?
            ORDER BY u.name ASC
            ''',
            (role,),
        ).fetchall()
    finally:
        conn.close()


def get_all_users():
    conn = get_db()
    try:
        return conn.execute(
            '''
            SELECT u.*,
                   dpa.name AS dpa_name
            FROM users u
            LEFT JOIN users dpa ON u.dpa_id = dpa.id
            ORDER BY u.role ASC, u.name ASC
            '''
        ).fetchall()
    finally:
        conn.close()


def get_dpas():
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE role = 'dpa' AND is_active = 1 ORDER BY name ASC"
        ).fetchall()
    finally:
        conn.close()


def get_lecturers():
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE role IN ('dosen', 'prodi', 'dpa') ORDER BY name ASC"
        ).fetchall()
    finally:
        conn.close()


def create_user(
    username: str,
    password: str,
    name: str,
    nim_nip: str,
    role: str,
    prodi: str,
    email: str = '',
    ipk: float = 0.0,
    semester: int = 0,
    dpa_id: int | None = None,
    prodi_code: str | None = None,
    status_sanksi: str = 'Aktif Bebas Sanksi',
) -> tuple[bool, str]:
    clean_username = (username or '').strip()
    clean_name = (name or '').strip()
    clean_nim_nip = (nim_nip or '').strip() or clean_username
    clean_email = (email or '').strip() or None
    if not clean_username or not clean_name or not password:
        return False, "Username, nama lengkap, dan password wajib diisi."
    if role not in VALID_ROLES:
        return False, f"Peran '{role}' tidak valid."

    clean_sanksi = (
        status_sanksi
        if status_sanksi in ('Aktif Bebas Sanksi', 'Sedang Sanksi')
        else 'Aktif Bebas Sanksi'
    )

    conn = get_db()
    try:
        resolved_prodi_name = (prodi or '').strip() or 'Teknik Informatika'
        resolved_prodi_code = (prodi_code or '').strip() or '60'
        if prodi_code:
            prog = conn.execute(
                "SELECT code, name FROM programs WHERE code = ?",
                (resolved_prodi_code,),
            ).fetchone()
            if prog:
                resolved_prodi_name = prog['name']

        if role == 'mahasiswa' and not dpa_id:
            default_dpa = conn.execute(
                "SELECT id FROM users WHERE role = 'dpa' ORDER BY id ASC LIMIT 1"
            ).fetchone()
            dpa_id = default_dpa['id'] if default_dpa else None

        avatar = '25110120414.png' if role == 'mahasiswa' else None
        conn.execute(
            '''
            INSERT INTO users (
                username, password, name, nim_nip, role, prodi, prodi_code,
                ipk, semester, status_sanksi, dpa_id, avatar, email, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''',
            (
                clean_username,
                generate_password_hash(password),
                clean_name,
                clean_nim_nip,
                role,
                resolved_prodi_name,
                resolved_prodi_code,
                ipk,
                semester,
                clean_sanksi,
                dpa_id,
                avatar,
                clean_email,
            ),
        )
        conn.commit()
        return True, f"Pengguna '{clean_name}' ({clean_username}) berhasil ditambahkan."
    except DB_INTEGRITY_ERRORS:
        conn.rollback()
        return False, f"Username '{clean_username}' sudah terdaftar."
    finally:
        conn.close()


def update_user(
    user_id: int,
    name: str,
    nim_nip: str,
    prodi: str,
    email: str = '',
    role: str | None = None,
    ipk: float | None = None,
    semester: int | None = None,
    new_password: str | None = None,
    is_active: int | None = None,
    dpa_id: int | None = None,
    prodi_code: str | None = None,
    status_sanksi: str | None = None,
) -> tuple[bool, str]:
    conn = get_db()
    try:
        existing = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not existing:
            return False, f"Pengguna #{user_id} tidak ditemukan."

        next_role = role if role in VALID_ROLES else existing['role']
        next_ipk = ipk if ipk is not None else existing['ipk']
        next_sem = semester if semester is not None else existing['semester']
        next_active = is_active if is_active in (0, 1) else existing['is_active']
        next_email = (email or '').strip() or None
        next_dpa_id = dpa_id if dpa_id is not None else existing['dpa_id']
        next_sanksi = (
            status_sanksi
            if status_sanksi in ('Aktif Bebas Sanksi', 'Sedang Sanksi')
            else (existing['status_sanksi'] or 'Aktif Bebas Sanksi')
        )

        next_prodi_code = (prodi_code or '').strip() or (existing['prodi_code'] or '60')
        next_prodi_name = (prodi or '').strip() or existing['prodi']
        if prodi_code:
            prog = conn.execute(
                "SELECT name FROM programs WHERE code = ?",
                (next_prodi_code,),
            ).fetchone()
            if prog:
                next_prodi_name = prog['name']

        next_password = (
            generate_password_hash(new_password)
            if (new_password or '').strip()
            else existing['password']
        )

        conn.execute(
            '''
            UPDATE users
            SET name = ?, nim_nip = ?, role = ?, prodi = ?, prodi_code = ?, ipk = ?,
                semester = ?, status_sanksi = ?, dpa_id = ?, email = ?, password = ?, is_active = ?
            WHERE id = ?
            ''',
            (
                (name or '').strip() or existing['name'],
                (nim_nip or '').strip() or existing['nim_nip'],
                next_role,
                next_prodi_name,
                next_prodi_code,
                next_ipk,
                next_sem,
                next_sanksi,
                next_dpa_id,
                next_email,
                next_password,
                next_active,
                user_id,
            ),
        )
        conn.commit()
        return True, f"Data pengguna '{(name or '').strip() or existing['name']}' berhasil diperbarui."
    finally:
        conn.close()


def delete_user(user_id: int) -> tuple[bool, str]:
    conn = get_db()
    try:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True, f"Pengguna #{user_id} berhasil dihapus."
    except DB_INTEGRITY_ERRORS:
        conn.rollback()
        return False, (
            f"Pengguna #{user_id} tidak dapat dihapus karena masih terkait dengan "
            "data KRS, mata kuliah, atau tagihan. Anda dapat menonaktifkannya jika perlu."
        )
    finally:
        conn.close()


def get_student_grades(student_id: int):
    conn = get_db()
    try:
        return conn.execute(
            '''
            SELECT sg.*, c.name AS course_name, c.sks
            FROM student_grades sg
            LEFT JOIN courses c ON sg.course_code = c.code
            WHERE sg.student_id = ?
            ORDER BY sg.semester_taken ASC, sg.course_code ASC
            ''',
            (student_id,),
        ).fetchall()
    finally:
        conn.close()


def get_student_grades_map(student_id: int) -> dict[str, dict]:
    rows = get_student_grades(student_id)
    return {row['course_code']: dict(row) for row in rows}


def upsert_student_grade(
    student_id: int,
    course_code: str,
    grade: str,
    semester_taken: int = 1,
) -> tuple[bool, str]:
    clean_code = (course_code or '').strip().upper()
    clean_grade = (grade or '').strip().upper()
    if not clean_code or clean_grade not in VALID_GRADES:
        return False, "Kode mata kuliah dan nilai huruf valid (A s.d. E) wajib diisi."

    conn = get_db()
    try:
        conn.execute(
            '''
            INSERT INTO student_grades (student_id, course_code, grade, semester_taken)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (student_id, course_code)
            DO UPDATE SET grade = excluded.grade, semester_taken = excluded.semester_taken
            ''',
            (student_id, clean_code, clean_grade, semester_taken),
        )
        conn.commit()
        return True, f"Riwayat nilai {clean_code} ({clean_grade}) berhasil disimpan."
    finally:
        conn.close()


def delete_student_grade(grade_id: int) -> None:
    conn = get_db()
    try:
        conn.execute("DELETE FROM student_grades WHERE id = ?", (grade_id,))
        conn.commit()
    finally:
        conn.close()
