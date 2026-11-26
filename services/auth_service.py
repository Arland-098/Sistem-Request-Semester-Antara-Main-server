import hmac
from werkzeug.security import check_password_hash

from database import get_db


def verify_password(stored_password: str, plain_password: str) -> bool:
    if not stored_password or plain_password is None:
        return False
    if stored_password.startswith(('scrypt:', 'pbkdf2:')):
        return check_password_hash(stored_password, plain_password)
    return hmac.compare_digest(stored_password, plain_password)


def authenticate_user(identifier: str, password: str):
    clean_id = (identifier or '').strip()
    if not clean_id or not password:
        return None, "Username/email dan password wajib diisi."

    conn = get_db()
    try:
        user = conn.execute(
            '''
            SELECT * FROM users
            WHERE LOWER(username) = LOWER(?)
               OR LOWER(COALESCE(email, '')) = LOWER(?)
               OR LOWER(nim_nip) = LOWER(?)
            LIMIT 1
            ''',
            (clean_id, clean_id, clean_id),
        ).fetchone()
    finally:
        conn.close()

    if not user or not verify_password(user['password'], password):
        return None, "Username/email atau password salah."

    if user['is_active'] == 0:
        return None, "Akun Anda sedang dinonaktifkan. Hubungi Super Admin."

    return user, None
