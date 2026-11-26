from werkzeug.security import generate_password_hash

from database import DB_INTEGRITY_ERRORS, get_db

VALID_ROLES = ('mahasiswa', 'dosen', 'kaprodi', 'admin_akademik', 'superadmin')


def get_user_by_id(user_id: int):
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()


def get_user_by_username(username: str):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    finally:
        conn.close()


def get_users_by_role(role: str):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE role = ? ORDER BY name ASC",
            (role,),
        ).fetchall()
    finally:
        conn.close()


def get_all_users():
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users ORDER BY role ASC, name ASC"
        ).fetchall()
    finally:
        conn.close()


def get_lecturers():
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE role IN ('dosen', 'kaprodi', 'dpa') ORDER BY name ASC"
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
) -> tuple[bool, str]:
    clean_username = (username or '').strip()
    clean_name = (name or '').strip()
    clean_nim_nip = (nim_nip or '').strip() or clean_username
    clean_email = (email or '').strip() or None
    if not clean_username or not clean_name or not password:
        return False, "Username, nama lengkap, dan password wajib diisi."
    if role not in VALID_ROLES:
        return False, f"Peran '{role}' tidak valid."

    conn = get_db()
    try:
        avatar = '25110120414.png' if role == 'mahasiswa' else None
        conn.execute(
            '''
            INSERT INTO users (
                username, password, name, nim_nip, role, prodi,
                ipk, semester, dpa_id, avatar, email, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''',
            (
                clean_username,
                generate_password_hash(password),
                clean_name,
                clean_nim_nip,
                role,
                (prodi or '').strip() or 'Teknik Informatika',
                ipk,
                semester,
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
        next_password = (
            generate_password_hash(new_password)
            if (new_password or '').strip()
            else existing['password']
        )

        conn.execute(
            '''
            UPDATE users
            SET name = ?, nim_nip = ?, role = ?, prodi = ?, ipk = ?,
                semester = ?, email = ?, password = ?, is_active = ?
            WHERE id = ?
            ''',
            (
                (name or '').strip() or existing['name'],
                (nim_nip or '').strip() or existing['nim_nip'],
                next_role,
                (prodi or '').strip() or existing['prodi'],
                next_ipk,
                next_sem,
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
