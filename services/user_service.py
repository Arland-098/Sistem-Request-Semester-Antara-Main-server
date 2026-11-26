from database import get_db


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


def get_lecturers():
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE role IN ('dosen', 'dpa') ORDER BY name ASC"
        ).fetchall()
    finally:
        conn.close()
