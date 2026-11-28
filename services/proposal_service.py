from database import DB_INTEGRITY_ERRORS, get_db


def get_programs(active_only: bool = False):
    conn = get_db()
    try:
        if active_only:
            return conn.execute(
                "SELECT * FROM programs WHERE status_buka_sa = 'Menyelenggarakan' ORDER BY code ASC"
            ).fetchall()
        return conn.execute("SELECT * FROM programs ORDER BY code ASC").fetchall()
    finally:
        conn.close()


def create_program(
    code: str,
    name: str,
    faculty: str,
    rumpun_ilmu: str = 'Sarjana Reguler',
    status_buka_sa: str = 'Menyelenggarakan',
) -> tuple[bool, str]:
    clean_code = (code or '').strip().upper()
    clean_name = (name or '').strip()
    clean_faculty = (faculty or '').strip() or 'Fakultas Sains dan Teknologi'
    if not clean_code or not clean_name:
        return False, "Kode dan nama Program Studi wajib diisi."

    clean_rumpun = (
        rumpun_ilmu
        if rumpun_ilmu in ('Sarjana Reguler', 'Ilmu Kesehatan')
        else 'Sarjana Reguler'
    )
    clean_status = (
        status_buka_sa
        if status_buka_sa in ('Menyelenggarakan', 'Tidak Buka')
        else 'Menyelenggarakan'
    )

    conn = get_db()
    try:
        conn.execute(
            '''
            INSERT INTO programs (code, name, faculty, rumpun_ilmu, status_buka_sa)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (clean_code, clean_name, clean_faculty, clean_rumpun, clean_status),
        )
        conn.commit()
        return True, f"Program Studi {clean_code} - {clean_name} berhasil ditambahkan."
    except DB_INTEGRITY_ERRORS:
        conn.rollback()
        return False, f"Kode Program Studi '{clean_code}' sudah terdaftar."
    finally:
        conn.close()


def update_program(
    code: str,
    name: str,
    faculty: str,
    rumpun_ilmu: str,
    status_buka_sa: str,
) -> tuple[bool, str]:
    conn = get_db()
    try:
        existing = conn.execute("SELECT * FROM programs WHERE code = ?", (code,)).fetchone()
        if not existing:
            return False, f"Program Studi '{code}' tidak ditemukan."
        conn.execute(
            '''
            UPDATE programs
            SET name = ?, faculty = ?, rumpun_ilmu = ?, status_buka_sa = ?
            WHERE code = ?
            ''',
            (
                (name or '').strip() or existing['name'],
                (faculty or '').strip() or existing['faculty'],
                rumpun_ilmu if rumpun_ilmu in ('Sarjana Reguler', 'Ilmu Kesehatan') else existing['rumpun_ilmu'],
                status_buka_sa if status_buka_sa in ('Menyelenggarakan', 'Tidak Buka') else existing['status_buka_sa'],
                code,
            ),
        )
        conn.commit()
        return True, f"Program Studi {code} berhasil diperbarui."
    finally:
        conn.close()


def get_announcements(active_only: bool = False):
    conn = get_db()
    try:
        where_clause = "WHERE a.is_active = 1" if active_only else ""
        return conn.execute(
            f'''
            SELECT a.*, u.name AS author_name
            FROM announcements a
            LEFT JOIN users u ON a.created_by = u.id
            {where_clause}
            ORDER BY a.is_active DESC, a.id DESC
            '''
        ).fetchall()
    finally:
        conn.close()


def create_announcement(title: str, content: str, category: str, created_by: int | None) -> tuple[bool, str]:
    clean_title = (title or '').strip()
    clean_content = (content or '').strip()
    if not clean_title or not clean_content:
        return False, "Judul dan isi pengumuman wajib diisi."

    conn = get_db()
    try:
        conn.execute(
            '''
            INSERT INTO announcements (title, content, category, is_active, created_by)
            VALUES (?, ?, ?, 1, ?)
            ''',
            (clean_title, clean_content, (category or '').strip() or 'Jadwal Resmi', created_by),
        )
        conn.commit()
        return True, f"Pengumuman '{clean_title}' berhasil dipublikasikan."
    finally:
        conn.close()


def toggle_announcement(ann_id: int) -> None:
    conn = get_db()
    try:
        row = conn.execute("SELECT is_active FROM announcements WHERE id = ?", (ann_id,)).fetchone()
        if row:
            next_val = 0 if row['is_active'] == 1 else 1
            conn.execute("UPDATE announcements SET is_active = ? WHERE id = ?", (next_val, ann_id))
            conn.commit()
    finally:
        conn.close()


def delete_announcement(ann_id: int) -> None:
    conn = get_db()
    try:
        conn.execute("DELETE FROM announcements WHERE id = ?", (ann_id,))
        conn.commit()
    finally:
        conn.close()


def get_equivalences():
    conn = get_db()
    try:
        return conn.execute(
            '''
            SELECT e.*,
                   pa.name AS prodi_asal_name,
                   pt.name AS prodi_tujuan_name
            FROM course_equivalences e
            LEFT JOIN programs pa ON e.prodi_asal_code = pa.code
            LEFT JOIN programs pt ON e.prodi_tujuan_code = pt.code
            ORDER BY e.id DESC
            '''
        ).fetchall()
    finally:
        conn.close()


def add_equivalence(
    kode_mk_asal: str,
    nama_mk_asal: str,
    prodi_asal_code: str,
    kode_mk_tujuan: str,
    nama_mk_tujuan: str,
    prodi_tujuan_code: str,
    sks: int = 3,
    status_ekuivalen: str = 'Valid',
) -> tuple[bool, str]:
    c_asal = (kode_mk_asal or '').strip().upper()
    n_asal = (nama_mk_asal or '').strip()
    c_tuj = (kode_mk_tujuan or '').strip().upper()
    n_tuj = (nama_mk_tujuan or '').strip()
    if not c_asal or not n_asal or not c_tuj or not n_tuj:
        return False, "Kode dan nama mata kuliah asal serta tujuan wajib diisi."

    conn = get_db()
    try:
        cnt = conn.execute("SELECT COUNT(*) AS cnt FROM course_equivalences").fetchone()['cnt']
        eq_code = f"EKV-{prodi_asal_code}-{prodi_tujuan_code}-{cnt + 1:02d}"
        conn.execute(
            '''
            INSERT INTO course_equivalences (
                equivalence_code, kode_mk_asal, nama_mk_asal, prodi_asal_code,
                kode_mk_tujuan, nama_mk_tujuan, prodi_tujuan_code, sks, status_ekuivalen
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (eq_code, c_asal, n_asal, prodi_asal_code, c_tuj, n_tuj, prodi_tujuan_code, sks, status_ekuivalen),
        )
        conn.commit()
        return True, f"Aturan ekuivalensi {c_asal} ↔ {c_tuj} berhasil disimpan."
    finally:
        conn.close()


def get_student_proposals(student_id: int):
    conn = get_db()
    try:
        return conn.execute(
            '''
            SELECT cp.*,
                   p.name AS target_prodi_name,
                   l.name AS assigned_lecturer_name
            FROM course_proposals cp
            LEFT JOIN programs p ON cp.target_prodi_code = p.code
            LEFT JOIN users l ON cp.lecturer_id = l.id
            WHERE cp.student_id = ?
            ORDER BY cp.id DESC
            ''',
            (student_id,),
        ).fetchall()
    finally:
        conn.close()


def get_all_proposals():
    conn = get_db()
    try:
        rows = conn.execute(
            '''
            SELECT cp.*,
                   u.name AS student_name,
                   u.nim_nip,
                   u.prodi AS student_prodi,
                   u.prodi_code AS student_prodi_code,
                   pt.name AS target_prodi_name,
                   l.name AS assigned_lecturer_name
            FROM course_proposals cp
            JOIN users u ON cp.student_id = u.id
            LEFT JOIN programs pt ON cp.target_prodi_code = pt.code
            LEFT JOIN users l ON cp.lecturer_id = l.id
            ORDER BY
                CASE cp.status WHEN 'Menunggu Persetujuan' THEN 0 WHEN 'Setuju' THEN 1 ELSE 2 END,
                cp.id DESC
            '''
        ).fetchall()

        counts_rows = conn.execute(
            '''
            SELECT UPPER(course_code) AS course_code, target_prodi_code, COUNT(*) AS supporter_count
            FROM course_proposals
            GROUP BY UPPER(course_code), target_prodi_code
            '''
        ).fetchall()
        counts_map = {
            (r['course_code'], r['target_prodi_code']): r['supporter_count']
            for r in counts_rows
        }

        result = []
        for row in rows:
            item = dict(row)
            key = (row['course_code'].upper(), row['target_prodi_code'])
            item['supporter_count'] = counts_map.get(key, 1)
            result.append(item)
        return result
    finally:
        conn.close()


def submit_course_proposal(
    student_id: int,
    target_prodi_code: str,
    course_code: str,
    course_name: str,
    sks: int,
    semester_target: int,
    is_cross_prodi: bool,
    origin_course_code: str = '',
    origin_course_name: str = '',
    syllabus_summary: str = '',
    reason: str = '',
) -> tuple[bool, str]:
    clean_code = (course_code or '').strip().upper()
    clean_name = (course_name or '').strip()
    clean_reason = (reason or '').strip()
    clean_syllabus = (syllabus_summary or '').strip()

    if not clean_code or not clean_name or not clean_reason:
        return False, "Kode MK, nama mata kuliah, dan alasan urgensi akademik wajib diisi."
    if sks < 1 or sks > 6:
        return False, "Bobot SKS mata kuliah usulan harus antara 1 s.d. 6 SKS."
    if is_cross_prodi and (not origin_course_code.strip() or not clean_syllabus):
        return False, "Untuk usulan Lintas Program Studi, kode mata kuliah asal & ringkasan silabus wajib diisi untuk verifikasi ekuivalensi."

    conn = get_db()
    try:
        cnt = conn.execute("SELECT COUNT(*) AS cnt FROM course_proposals").fetchone()['cnt']
        proposal_code = f"USL-2026-{cnt + 1:04d}"

        conn.execute(
            '''
            INSERT INTO course_proposals (
                proposal_code, student_id, target_prodi_code, course_code, course_name,
                sks, semester_target, is_cross_prodi, origin_course_code, origin_course_name,
                syllabus_summary, reason, status, prodi_asal_status, prodi_tujuan_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Menunggu Persetujuan', ?, 'Menunggu')
            ''',
            (
                proposal_code,
                student_id,
                (target_prodi_code or '60').strip(),
                clean_code,
                clean_name,
                sks,
                semester_target,
                1 if is_cross_prodi else 0,
                (origin_course_code or '').strip().upper() or None,
                (origin_course_name or '').strip() or None,
                clean_syllabus or None,
                clean_reason,
                'Setuju' if not is_cross_prodi else 'Menunggu',
            ),
        )
        conn.commit()
        return True, (
            f"Usulan mata kuliah {clean_code} - {clean_name} ({proposal_code}) berhasil dikirim ke Program Studi."
        )
    finally:
        conn.close()


def review_course_proposal(
    proposal_id: int,
    decision: str,
    admin_notes: str = '',
    lecturer_id: int | None = None,
    schedule_day: str = 'Senin',
    schedule_time: str = '08.00 - 10.30 WIB',
    room: str = 'Ruang Kelas 3.01 FST',
    quota: int = 30,
    publish_to_catalog: bool = True,
) -> tuple[bool, str]:
    conn = get_db()
    try:
        prop = conn.execute(
            "SELECT * FROM course_proposals WHERE id = ?",
            (proposal_id,),
        ).fetchone()
        if not prop:
            return False, f"Usulan #{proposal_id} tidak ditemukan."

        if decision == 'reject':
            note = (admin_notes or '').strip() or 'Usulan ditolak setelah tinjauan kurikulum/kapasitas Prodi.'
            conn.execute(
                '''
                UPDATE course_proposals
                SET status = 'Tolak',
                    prodi_asal_status = CASE WHEN is_cross_prodi = 1 THEN 'Tolak' ELSE prodi_asal_status END,
                    prodi_tujuan_status = 'Tolak',
                    admin_notes = ?,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                (note, proposal_id),
            )
            conn.commit()
            return True, f"Usulan {prop['proposal_code']} ({prop['course_code']}) telah ditolak."

        # Approve proposal & optionally publish into official courses catalog
        lecturer_name = 'Akan Ditugaskan Prodi'
        if lecturer_id:
            lec = conn.execute("SELECT name FROM users WHERE id = ?", (lecturer_id,)).fetchone()
            if lec:
                lecturer_name = lec['name']

        prog = conn.execute(
            "SELECT name FROM programs WHERE code = ?",
            (prop['target_prodi_code'],),
        ).fetchone()
        prodi_name = prog['name'] if prog else 'Teknik Informatika'

        note = (admin_notes or '').strip() or 'Disetujui & dibuka pada katalog resmi Semester Antara.'
        conn.execute(
            '''
            UPDATE course_proposals
            SET status = 'Setuju',
                prodi_asal_status = 'Setuju',
                prodi_tujuan_status = 'Setuju',
                lecturer_id = ?,
                admin_notes = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''',
            (lecturer_id, note, proposal_id),
        )

        published_msg = ""
        if publish_to_catalog:
            existing_course = conn.execute(
                "SELECT id FROM courses WHERE code = ?",
                (prop['course_code'],),
            ).fetchone()
            if not existing_course:
                conn.execute(
                    '''
                    INSERT INTO courses (
                        code, name, sks, schedule_day, schedule_time, room, quota, min_quota,
                        lecturer_id, lecturer_name, prodi_code, prodi_name,
                        status, lecturer_agreed, semester, class_name, wp_type
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 10, ?, ?, ?, ?, 'Ditawarkan', ?, ?, ?, ?)
                    ''',
                    (
                        prop['course_code'],
                        prop['course_name'],
                        prop['sks'],
                        schedule_day or 'Senin',
                        schedule_time or '08.00 - 10.30 WIB',
                        room or 'Ruang Kelas 3.01 FST',
                        quota,
                        lecturer_id,
                        lecturer_name,
                        prop['target_prodi_code'],
                        prodi_name,
                        1 if lecturer_id else 0,
                        prop['semester_target'] or 1,
                        f"{prop['semester_target'] or 1}SA",
                        'P',
                    ),
                )
                published_msg = " dan diterbitkan ke Katalog Resmi"
            else:
                published_msg = " (mata kuliah sudah ada di Katalog Resmi)"

            if prop['is_cross_prodi'] == 1 and prop['origin_course_code']:
                student_row = conn.execute(
                    "SELECT prodi_code FROM users WHERE id = ?",
                    (prop['student_id'],),
                ).fetchone()
                origin_prodi = (student_row['prodi_code'] if student_row else None) or '60'
                eq_exists = conn.execute(
                    '''
                    SELECT 1 FROM course_equivalences
                    WHERE kode_mk_asal = ? AND kode_mk_tujuan = ?
                    ''',
                    (prop['origin_course_code'], prop['course_code']),
                ).fetchone()
                if not eq_exists:
                    cnt = conn.execute("SELECT COUNT(*) AS cnt FROM course_equivalences").fetchone()['cnt']
                    conn.execute(
                        '''
                        INSERT INTO course_equivalences (
                            equivalence_code, kode_mk_asal, nama_mk_asal, prodi_asal_code,
                            kode_mk_tujuan, nama_mk_tujuan, prodi_tujuan_code, sks, status_ekuivalen
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Valid')
                        ''',
                        (
                            f"EKV-{origin_prodi}-{prop['target_prodi_code']}-{cnt + 1:02d}",
                            prop['origin_course_code'],
                            prop['origin_course_name'] or prop['course_name'],
                            origin_prodi,
                            prop['course_code'],
                            prop['course_name'],
                            prop['target_prodi_code'],
                            prop['sks'],
                        ),
                    )

        conn.commit()
        return True, f"Usulan {prop['proposal_code']} ({prop['course_code']}) disetujui{published_msg}."
    finally:
        conn.close()
