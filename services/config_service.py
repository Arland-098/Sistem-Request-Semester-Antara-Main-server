from database import get_db


def get_config(key: str, default: str | None = None) -> str | None:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT value FROM system_config WHERE key = ?",
            (key,),
        ).fetchone()
        return row['value'] if row else default
    finally:
        conn.close()


def set_config(key: str, value: object) -> None:
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO system_config (key, value) VALUES (?, ?)
            ON CONFLICT (key) DO UPDATE SET value = excluded.value
            """,
            (key, str(value)),
        )
        conn.commit()
    finally:
        conn.close()
