from database import get_db


def get_all_invoices():
    conn = get_db()
    try:
        return conn.execute('''
        SELECT inv.*, u.name AS student_name, u.nim_nip, u.prodi, ka.total_sks, ka.semester_period
        FROM invoices inv
        JOIN users u ON inv.student_id = u.id
        JOIN krs_applications ka ON inv.application_id = ka.id
        ORDER BY inv.created_at DESC, inv.id DESC
        ''').fetchall()
    finally:
        conn.close()


def reconcile_manual_payment(invoice_id: int, ref_no: str, notes: str) -> None:
    conn = get_db()
    try:
        conn.execute('''
        UPDATE invoices
        SET status = 'Lunas',
            paid_at = CURRENT_TIMESTAMP,
            payment_channel = 'Rekonsiliasi Manual Bank',
            reconciliation_notes = ?
        WHERE id = ?
        ''', (f"Ref: {ref_no} | {notes}", invoice_id))

        inv = conn.execute(
            "SELECT application_id FROM invoices WHERE id = ?",
            (invoice_id,),
        ).fetchone()
        if inv:
            conn.execute(
                "UPDATE krs_applications SET status = 'Lunas' WHERE id = ?",
                (inv['application_id'],),
            )

        conn.commit()
    finally:
        conn.close()


def get_official_participants():
    conn = get_db()
    try:
        return conn.execute('''
        SELECT u.nim_nip, u.name AS student_name, u.prodi,
               c.code AS course_code, c.name AS course_name, c.sks, c.room,
               c.schedule_day, c.schedule_time, c.lecturer_name, c.status AS class_status,
               ka.status AS krs_status,
               COALESCE(inv.status, 'Belum Terbit Tagihan') AS payment_status,
               inv.va_number
        FROM krs_items ki
        JOIN courses c ON ki.course_id = c.id
        JOIN krs_applications ka ON ki.application_id = ka.id
        JOIN users u ON ka.student_id = u.id
        LEFT JOIN invoices inv ON ka.id = inv.application_id
        WHERE ki.status = 'Aktif'
        ORDER BY c.code ASC, u.nim_nip ASC
        ''').fetchall()
    finally:
        conn.close()
