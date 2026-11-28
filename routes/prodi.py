import csv
import io
from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from routes.decorators import get_logged_in_user, roles_required
from services import (
    add_course,
    add_equivalence,
    close_registration_and_mark_classes,
    create_announcement,
    delete_announcement,
    delete_course,
    get_all_proposals,
    get_announcements,
    get_courses_list,
    get_equivalences,
    get_lecturers,
    get_official_participants,
    get_programs,
    request_class_dispensation,
    review_course_proposal,
    set_config,
    toggle_announcement,
    update_course_details,
    update_course_schedule,
    update_course_status,
)

prodi_bp = Blueprint('prodi', __name__, url_prefix='/prodi')


def _safe_int(value, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# --- FR-13: PENGUMUMAN & JADWAL RESMI ---

@prodi_bp.route('/pengumuman')
@roles_required('prodi')
def pengumuman():
    announcements = get_announcements(active_only=False)
    return render_template(
        'prodi_pengumuman.html',
        announcements=announcements,
        active_tab='prodi_pengumuman',
    )


@prodi_bp.route('/pengumuman/add', methods=['POST'])
@roles_required('prodi')
def pengumuman_add():
    user = get_logged_in_user()
    success, message = create_announcement(
        title=request.form.get('title', ''),
        content=request.form.get('content', ''),
        category=request.form.get('category', 'Jadwal Resmi'),
        created_by=user['id'] if user else None,
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('prodi.pengumuman'))


@prodi_bp.route('/pengumuman/toggle/<int:ann_id>', methods=['POST'])
@roles_required('prodi')
def pengumuman_toggle(ann_id: int):
    toggle_announcement(ann_id)
    flash("Status tampilan pengumuman berhasil diperbarui.", "info")
    return redirect(url_for('prodi.pengumuman'))


@prodi_bp.route('/pengumuman/delete/<int:ann_id>', methods=['POST'])
@roles_required('prodi')
def pengumuman_delete(ann_id: int):
    delete_announcement(ann_id)
    flash("Pengumuman telah dihapus.", "warning")
    return redirect(url_for('prodi.pengumuman'))


# --- FR-14: PERIODE PENDAFTARAN & KEAKTIFAN SA ---

@prodi_bp.route('/periode')
@roles_required('prodi')
def periode():
    return render_template('prodi_periode.html', active_tab='prodi_periode')


@prodi_bp.route('/periode/update', methods=['POST'])
@roles_required('prodi')
def periode_update():
    set_config('active_semester', request.form.get('active_semester', 'Semester Antara 2026/2027'))
    next_status = request.form.get('registration_status', 'Buka')
    set_config('proposal_start', request.form.get('proposal_start', '2026-06-20'))
    set_config('proposal_end', request.form.get('proposal_end', '2026-06-30'))
    set_config('registration_start', request.form.get('registration_start', '2026-07-01'))
    set_config('registration_end', request.form.get('registration_end', '2026-07-25'))
    set_config('payment_start', request.form.get('payment_start', '2026-07-26'))
    set_config('payment_end', request.form.get('payment_end', '2026-08-05'))
    set_config('max_sks', _safe_int(request.form.get('max_sks'), 9))
    set_config('min_quota', _safe_int(request.form.get('min_quota'), 10))

    if next_status == 'Tutup':
        ready_cnt, under_cnt = close_registration_and_mark_classes()
        flash(
            f"Periode pendaftaran DITUTUP (Auto-Check 3). {ready_cnt} kelas memenuhi kuota >= 10 dan "
            f"{under_cnt} kelas ditandai Menunggu Kebijakan Prodi.",
            "warning",
        )
    else:
        set_config('registration_status', 'Buka')
        flash("Pengaturan periode pendaftaran Semester Antara berhasil diperbarui (BUKA).", "success")

    return redirect(url_for('prodi.periode'))


# --- FR-15 & FR-16 & AD-01: REKAP USULAN MK & EKUIVALENSI LINTAS PRODI ---

@prodi_bp.route('/usulan')
@roles_required('prodi')
def usulan():
    proposals = get_all_proposals()
    equivalences = get_equivalences()
    lecturers = get_lecturers()
    programs = get_programs(active_only=False)
    return render_template(
        'prodi_usulan.html',
        proposals=proposals,
        equivalences=equivalences,
        lecturers=lecturers,
        programs=programs,
        active_tab='prodi_usulan',
    )


@prodi_bp.route('/usulan/review/<int:proposal_id>', methods=['POST'])
@roles_required('prodi')
def usulan_review(proposal_id: int):
    decision = request.form.get('decision', 'approve')
    admin_notes = request.form.get('admin_notes', '')
    lecturer_id = _safe_int(request.form.get('lecturer_id'))
    schedule_day = request.form.get('schedule_day', 'Senin')
    schedule_time = request.form.get('schedule_time', '08.00 - 10.30 WIB')
    room = request.form.get('room', 'Ruang Kelas 3.01 FST')
    quota = _safe_int(request.form.get('quota'), 30) or 30
    publish_to_catalog = request.form.get('publish_to_catalog') == '1'

    success, message = review_course_proposal(
        proposal_id=proposal_id,
        decision=decision,
        admin_notes=admin_notes,
        lecturer_id=lecturer_id,
        schedule_day=schedule_day,
        schedule_time=schedule_time,
        room=room,
        quota=quota,
        publish_to_catalog=publish_to_catalog,
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('prodi.usulan'))


@prodi_bp.route('/ekuivalensi/add', methods=['POST'])
@roles_required('prodi')
def ekuivalensi_add():
    success, message = add_equivalence(
        kode_mk_asal=request.form.get('kode_mk_asal', ''),
        nama_mk_asal=request.form.get('nama_mk_asal', ''),
        prodi_asal_code=request.form.get('prodi_asal_code', '60'),
        kode_mk_tujuan=request.form.get('kode_mk_tujuan', ''),
        nama_mk_tujuan=request.form.get('nama_mk_tujuan', ''),
        prodi_tujuan_code=request.form.get('prodi_tujuan_code', '55'),
        sks=_safe_int(request.form.get('sks'), 3) or 3,
        status_ekuivalen=request.form.get('status_ekuivalen', 'Valid'),
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('prodi.usulan'))


# --- FR-17: KATALOG MATA KULIAH & KUOTA ---

@prodi_bp.route('/katalog')
@roles_required('prodi')
def katalog():
    courses = get_courses_list(prodi_code='ALL')
    lecturers = get_lecturers()
    programs = get_programs(active_only=False)
    return render_template(
        'prodi_katalog.html',
        courses=courses,
        lecturers=lecturers,
        programs=programs,
        active_tab='prodi_katalog',
    )


@prodi_bp.route('/katalog/add', methods=['POST'])
@roles_required('prodi')
def katalog_add():
    code = request.form.get('code', '')
    name = request.form.get('name', '')
    sks = _safe_int(request.form.get('sks'), 3) or 3
    quota = _safe_int(request.form.get('quota'), 30) or 30
    lecturer_id = _safe_int(request.form.get('lecturer_id'))
    schedule_day = request.form.get('schedule_day', 'Senin')
    schedule_time = request.form.get('schedule_time', '08.00 - 10.30 WIB')
    room = request.form.get('room', 'Ruang Kelas FST')
    semester = _safe_int(request.form.get('semester'), 1) or 1
    class_name = (request.form.get('class_name') or '').strip() or f'{semester}ATI'
    wp_type = (request.form.get('wp_type') or 'W').strip().upper()
    prodi_code = (request.form.get('prodi_code') or '60').strip()

    success, message = add_course(
        code,
        name,
        sks,
        schedule_day,
        schedule_time,
        room,
        quota,
        lecturer_id,
        semester=semester,
        class_name=class_name,
        wp_type=wp_type,
        prodi_code=prodi_code,
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('prodi.katalog'))


@prodi_bp.route('/katalog/edit/<int:course_id>', methods=['POST'])
@roles_required('prodi')
def katalog_edit(course_id: int):
    name = request.form.get('name', '')
    sks = _safe_int(request.form.get('sks'), 3) or 3
    quota = _safe_int(request.form.get('quota'), 30) or 30
    lecturer_id = _safe_int(request.form.get('lecturer_id'))
    schedule_day = request.form.get('schedule_day', 'Senin')
    schedule_time = request.form.get('schedule_time', '08.00 - 10.30 WIB')
    room = request.form.get('room', 'Ruang Kelas FST')
    semester = _safe_int(request.form.get('semester'))
    class_name = (request.form.get('class_name') or '').strip() or None
    wp_type = (request.form.get('wp_type') or '').strip().upper() or None
    prodi_code = (request.form.get('prodi_code') or '').strip() or None

    success, message = update_course_details(
        course_id,
        name,
        sks,
        schedule_day,
        schedule_time,
        room,
        quota,
        lecturer_id,
        semester=semester,
        class_name=class_name,
        wp_type=wp_type,
        prodi_code=prodi_code,
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('prodi.katalog'))


@prodi_bp.route('/katalog/delete/<int:course_id>', methods=['POST'])
@roles_required('prodi')
def katalog_delete(course_id: int):
    success, message = delete_course(course_id)
    flash(message, 'warning' if success else 'danger')
    return redirect(url_for('prodi.katalog'))


# --- FR-18: JADWAL KULIAH LURING & RUANG KELAS ---

@prodi_bp.route('/jadwal_ruang')
@roles_required('prodi')
def jadwal_ruang():
    courses = get_courses_list(prodi_code='ALL')
    return render_template('prodi_jadwal_ruang.html', courses=courses, active_tab='prodi_jadwal')


@prodi_bp.route('/jadwal/update/<int:course_id>', methods=['POST'])
@roles_required('prodi')
def jadwal_update(course_id: int):
    day = request.form.get('schedule_day', 'Senin')
    time_str = request.form.get('schedule_time', '08.00 - 10.30 WIB')
    room = request.form.get('room', 'Ruang Kelas FST')

    update_course_schedule(course_id, day, time_str, room)
    flash("Jadwal dan alokasi ruang kuliah luring berhasil diperbarui.", "success")
    return redirect(url_for('prodi.jadwal_ruang'))


# --- FR-19 & UC-PRD-07 & SD-03: EVALUASI KUOTA, DISPENSASI & PENETAPAN STATUS KELAS ---

@prodi_bp.route('/monitoring')
@roles_required('prodi')
def monitoring():
    courses = get_courses_list(prodi_code='ALL')
    return render_template('prodi_monitoring.html', courses=courses, active_tab='prodi_monitoring')


@prodi_bp.route('/dispensasi/request/<int:course_id>', methods=['POST'])
@roles_required('prodi')
def request_dispensasi(course_id: int):
    success, message = request_class_dispensation(course_id)
    flash(message, 'info' if success else 'danger')
    return redirect(url_for('prodi.monitoring'))


@prodi_bp.route('/status/<int:course_id>', methods=['POST'])
@roles_required('prodi')
def set_class_status(course_id: int):
    new_status = request.form.get('status', 'Ditawarkan')
    success, message = update_course_status(course_id, new_status)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('prodi.monitoring'))


# --- FR-20: PENUTUPAN PENDAFTARAN & EKSPOR PESERTA ---

@prodi_bp.route('/rekap')
@roles_required('prodi')
def rekap():
    participants = get_official_participants()
    return render_template('prodi_rekap.html', participants=participants, active_tab='prodi_rekap')


@prodi_bp.route('/tutup', methods=['POST'])
@roles_required('prodi')
def tutup():
    ready_cnt, under_cnt = close_registration_and_mark_classes()
    flash(
        f"Pendaftaran Semester Antara resmi DITUTUP (Auto-Check 3). {ready_cnt} kelas memenuhi kuota minimal 10 "
        f"dan {under_cnt} kelas di bawah 10 pendaftar ditandai Menunggu Kebijakan Prodi.",
        "warning",
    )
    return redirect(url_for('prodi.monitoring'))


@prodi_bp.route('/buka', methods=['POST'])
@roles_required('prodi')
def buka():
    set_config('registration_status', 'Buka')
    flash("Pendaftaran Semester Antara telah DIBUKA kembali.", "success")
    return redirect(url_for('prodi.rekap'))


@prodi_bp.route('/export_csv')
@roles_required('prodi')
def export_csv():
    participants = get_official_participants()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'NO', 'NIM', 'NAMA MAHASISWA', 'PROGRAM STUDI', 'DOSEN PA (DPA)',
        'KODE MK', 'NAMA MATA KULIAH', 'SKS', 'JENIS AMBIL', 'RUANG KELAS',
        'HARI', 'WAKTU', 'DOSEN PENGAMPU', 'STATUS KELAS', 'STATUS KRS',
        'STATUS PEMBAYARAN', 'BANK MITRA', 'NO VIRTUAL ACCOUNT',
    ])

    for index, participant in enumerate(participants, 1):
        writer.writerow([
            index,
            participant['nim_nip'],
            participant['student_name'],
            participant['prodi'],
            participant['dpa_name'] or '-',
            participant['course_code'],
            participant['course_name'],
            participant['sks'],
            participant['jenis_pengambilan'],
            participant['room'],
            participant['schedule_day'],
            participant['schedule_time'],
            participant['lecturer_name'],
            participant['class_status'],
            participant['krs_status'],
            participant['payment_status'],
            participant['bank_name'] or '-',
            participant['va_number'] or '-',
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': 'attachment;filename=Rekapitulasi_Peserta_Semester_Antara_2026.csv'
        },
    )
