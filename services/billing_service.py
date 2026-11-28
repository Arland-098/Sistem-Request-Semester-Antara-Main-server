import datetime
import random

from database import get_db

PARTNER_BANKS = ('Bank Mandiri', 'BNI', 'BRI', 'BTN', 'BSI')
OPEN_CLASS_STATUSES = ('Dibuka', 'Dispensasi Buka')
PENDING_CLASS_STATUSES = ('Menunggu', 'Ditawarkan', 'Menunggu Kebijakan Prodi')


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


def _get_config_map(conn) -> dict[str, str]:
    rows = conn.execute("SELECT key, value FROM system_config").fetchall()
    return {r['key']: r['value'] for r in rows}


def _get_student_rate_in_tx(conn, student_id: int, cfg: dict[str, str]) -> int:
    row = conn.execute(
        '''
        SELECT COALESCE(p.rumpun_ilmu, 'Sarjana Reguler') AS rumpun_ilmu
        FROM users u
        LEFT JOIN programs p ON u.prodi_code = p.code
        WHERE u.id = ?
        ''',
        (student_id,),
    ).fetchone()
    rumpun = row['rumpun_ilmu'] if row else 'Sarjana Reguler'
    if rumpun == 'Ilmu Kesehatan':
        return int(cfg.get('sks_rate_kesehatan', '850000') or 850000)
    return int(cfg.get('sks_rate', '220000') or 220000)


def issue_invoice_if_eligible_in_tx(conn, application_id: int) -> tuple[bool, str]:
    """
    BR-08 & BR-07:
    Terbitkan / perbarui tagihan VA HANYA JIKA:
    1. KRS sudah 'Disetujui DPA'
    2. Periode pendaftaran sudah ditutup ('Tutup')
    3. Seluruh mata kuliah aktif pada KRS tidak lagi menunggu evaluasi Prodi
       (sudah final: 'Dibuka' atau 'Dispensasi Buka').
    """
    cfg = _get_config_map(conn)
    if cfg.get('registration_status', 'Buka') != 'Tutup':
        return False, "Menunggu penutupan periode pendaftaran."

    app_row = conn.execute(
        "SELECT * FROM krs_applications WHERE id = ?",
        (application_id,),
    ).fetchone()
    if not app_row or app_row['status'] != 'Disetujui DPA':
        return False, "Pengajuan belum berstatus Disetujui DPA."

    items = conn.execute(
        '''
        SELECT ki.id, ki.status AS item_status, c.sks, c.status AS class_status
        FROM krs_items ki
        JOIN courses c ON ki.course_id = c.id
        WHERE ki.application_id = ? AND ki.status = 'Aktif'
        ''',
        (application_id,),
    ).fetchall()

    if not items:
        conn.execute(
            "UPDATE krs_applications SET status = 'Dibatalkan', status_final = 'Dibatalkan', total_sks = 0 WHERE id = ?",
            (application_id,),
        )
        conn.execute(
            "DELETE FROM invoices WHERE application_id = ? AND status = 'Belum Lunas'",
            (application_id,),
        )
        return False, "Seluruh kelas pada pengajuan telah dibatalkan."

    if any(item['class_status'] in PENDING_CLASS_STATUSES for item in items):
        conn.execute(
            "UPDATE krs_applications SET status_final = 'Menunggu Kepastian Kelas Buka' WHERE id = ?",
            (application_id,),
        )
        return False, "Sebagian mata kuliah masih menunggu penetapan status kelas oleh Program Studi."

    open_items = [item for item in items if item['class_status'] in OPEN_CLASS_STATUSES]
    if not open_items:
        conn.execute(
            "UPDATE krs_applications SET status = 'Dibatalkan', status_final = 'Dibatalkan', total_sks = 0 WHERE id = ?",
            (application_id,),
        )
        conn.execute(
            "DELETE FROM invoices WHERE application_id = ? AND status = 'Belum Lunas'",
            (application_id,),
        )
        return False, "Tidak ada kelas aktif yang dibuka."

    total_sks = sum(item['sks'] for item in open_items)
    sks_rate = _get_student_rate_in_tx(conn, app_row['student_id'], cfg)
    amount = total_sks * sks_rate

    existing_inv = conn.execute(
        "SELECT * FROM invoices WHERE application_id = ?",
        (application_id,),
    ).fetchone()

    if existing_inv:
        if existing_inv['status'] == 'Belum Lunas':
            conn.execute(
                "UPDATE invoices SET amount = ? WHERE id = ?",
                (amount, existing_inv['id']),
            )
            conn.execute(
                "UPDATE krs_applications SET total_sks = ?, status_final = 'Menunggu Pembayaran' WHERE id = ?",
                (total_sks, application_id),
            )
            return True, f"Tagihan VA #{existing_inv['va_number']} diperbarui."
        return False, "Tagihan sudah diproses sebelumnya."

    student = conn.execute(
        "SELECT nim_nip FROM users WHERE id = ?",
        (app_row['student_id'],),
    ).fetchone()
    nim = student['nim_nip'] if student else '000000'
    va_number = _generate_unique_va(conn, nim)

    bank_name = app_row['preferred_bank'] if app_row['preferred_bank'] in PARTNER_BANKS else 'Bank Mandiri'
    payment_end = cfg.get('payment_end', '2026-08-05') or '2026-08-05'
    expires_at = f"{payment_end} 23:59:59"

    conn.execute(
        '''
        INSERT INTO invoices (
            application_id, student_id, va_number, bank_name, amount, status, expires_at
        )
        VALUES (?, ?, ?, ?, ?, 'Belum Lunas', ?)
        ''',
        (application_id, app_row['student_id'], va_number, bank_name, amount, expires_at),
    )
    conn.execute(
        "UPDATE krs_applications SET total_sks = ?, status_final = 'Menunggu Pembayaran' WHERE id = ?",
        (total_sks, application_id),
    )
    return True, f"Tagihan VA {va_number} ({bank_name}) berhasil diterbitkan."


def issue_invoice_if_eligible(application_id: int) -> tuple[bool, str]:
    conn = get_db()
    try:
        issued, msg = issue_invoice_if_eligible_in_tx(conn, application_id)
        conn.commit()
        return issued, msg
    finally:
        conn.close()


def sync_invoices_for_ready_applications() -> int:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id FROM krs_applications WHERE status = 'Disetujui DPA'"
        ).fetchall()
        issued_count = 0
        for row in rows:
            issued, _ = issue_invoice_if_eligible_in_tx(conn, row['id'])
            if issued:
                issued_count += 1
        conn.commit()
        return issued_count
    finally:
        conn.close()


def get_all_invoices():
    conn = get_db()
    try:
        return conn.execute(
            '''
            SELECT inv.*,
                   u.name AS student_name,
                   u.nim_nip,
                   u.prodi,
                   COALESCE(p.rumpun_ilmu, 'Sarjana Reguler') AS rumpun_ilmu,
                   ka.total_sks,
                   ka.semester_period,
                   ka.status AS krs_status,
                   ka.status_final
            FROM invoices inv
            JOIN users u ON inv.student_id = u.id
            LEFT JOIN programs p ON u.prodi_code = p.code
            JOIN krs_applications ka ON inv.application_id = ka.id
            ORDER BY inv.created_at DESC, inv.id DESC
            '''
        ).fetchall()
    finally:
        conn.close()


def reconcile_manual_payment(invoice_id: int, ref_no: str, notes: str) -> tuple[bool, str]:
    conn = get_db()
    try:
        inv = conn.execute(
            "SELECT * FROM invoices WHERE id = ?",
            (invoice_id,),
        ).fetchone()
        if not inv:
            return False, f"Faktur #{invoice_id} tidak ditemukan."
        if inv['status'] == 'Expired':
            return False, "Tagihan ini sudah berstatus Expired / Gugur sesuai BR-10 dan tidak dapat dilunasi."

        conn.execute(
            '''
            UPDATE invoices
            SET status = 'Lunas',
                paid_at = CURRENT_TIMESTAMP,
                payment_channel = 'Rekonsiliasi Manual Bank',
                reconciliation_notes = ?
            WHERE id = ?
            ''',
            (f"Ref: {ref_no} | {notes}", invoice_id),
        )
        conn.execute(
            "UPDATE krs_applications SET status = 'Lunas', status_final = 'Terdaftar Resmi' WHERE id = ?",
            (inv['application_id'],),
        )
        conn.commit()
        return True, f"Pembayaran Virtual Account faktur #{invoice_id} berhasil DIREKONSILIASI LUNAS."
    finally:
        conn.close()


def _expire_invoice_in_tx(conn, inv_row, reason: str) -> None:
    conn.execute(
        '''
        UPDATE invoices
        SET status = 'Expired',
            reconciliation_notes = ?
        WHERE id = ?
        ''',
        (reason, inv_row['id']),
    )
    conn.execute(
        '''
        UPDATE krs_applications
        SET status = 'Expired',
            status_final = 'Gugur / Expired'
        WHERE id = ?
        ''',
        (inv_row['application_id'],),
    )
    conn.execute(
        "UPDATE krs_items SET status = 'Gugur' WHERE application_id = ? AND status = 'Aktif'",
        (inv_row['application_id'],),
    )


def expire_invoice(invoice_id: int, reason: str = 'Melewati batas waktu pembayaran (BR-10).') -> tuple[bool, str]:
    conn = get_db()
    try:
        inv = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
        if not inv:
            return False, f"Faktur #{invoice_id} tidak ditemukan."
        if inv['status'] == 'Lunas':
            return False, "Tagihan yang sudah Lunas tidak dapat diubah menjadi Expired."
        _expire_invoice_in_tx(conn, inv, reason)
        conn.commit()
        return True, f"Tagihan #{invoice_id} diubah menjadi EXPIRED; kepesertaan mahasiswa dinyatakan Gugur (BR-10)."
    finally:
        conn.close()


def _parse_dt(val) -> datetime.datetime | None:
    if not val:
        return None
    if isinstance(val, datetime.datetime):
        return val
    text = str(val).strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def process_expired_invoices() -> tuple[int, str]:
    """Auto-Check 5 / BR-10: Tandai Expired tagihan Belum Lunas yang telah melewati WaktuExpired."""
    conn = get_db()
    try:
        now = datetime.datetime.now()
        pending = conn.execute(
            "SELECT * FROM invoices WHERE status = 'Belum Lunas'"
        ).fetchall()
        expired_count = 0
        for inv in pending:
            exp_dt = _parse_dt(inv['expires_at'])
            if exp_dt and exp_dt < now:
                _expire_invoice_in_tx(
                    conn,
                    inv,
                    f"Auto-Check 5: Kedaluwarsa melewati batas {inv['expires_at']}",
                )
                expired_count += 1
        conn.commit()
        if expired_count:
            return expired_count, f"Auto-Check 5 selesai: {expired_count} tagihan kedaluwarsa ditandai Expired & kepesertaan digugurkan."
        return 0, "Auto-Check 5 selesai: tidak ada tagihan Belum Lunas yang melewati batas waktu pembayaran."
    finally:
        conn.close()


def get_official_participants():
    conn = get_db()
    try:
        return conn.execute(
            '''
            SELECT u.nim_nip, u.name AS student_name, u.prodi,
                   dpa.name AS dpa_name,
                   c.code AS course_code, c.name AS course_name, c.sks, c.room,
                   c.schedule_day, c.schedule_time, c.lecturer_name, c.status AS class_status,
                   ka.status AS krs_status,
                   ka.status_final,
                   ki.jenis_pengambilan,
                   COALESCE(inv.status, 'Belum Terbit Tagihan') AS payment_status,
                   inv.va_number,
                   inv.bank_name
            FROM krs_items ki
            JOIN courses c ON ki.course_id = c.id
            JOIN krs_applications ka ON ki.application_id = ka.id
            JOIN users u ON ka.student_id = u.id
            LEFT JOIN users dpa ON u.dpa_id = dpa.id
            LEFT JOIN invoices inv ON ka.id = inv.application_id
            WHERE ki.status = 'Aktif' AND ka.status NOT IN ('Dibatalkan', 'Expired')
            ORDER BY c.code ASC, u.nim_nip ASC
            '''
        ).fetchall()
    finally:
        conn.close()
