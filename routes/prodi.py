import csv
import io
from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from services import (
    add_course,
    delete_course,
    get_courses_list,
    get_lecturers,
    get_official_participants,
    set_config,
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


@prodi_bp.route('/periode')
def periode():
    return render_template('prodi_periode.html', active_tab='prodi_periode')


@prodi_bp.route('/periode/update', methods=['POST'])
def periode_update():
    set_config('active_semester', request.form.get('active_semester', 'Semester Antara 2026/2027'))
    set_config('registration_status', request.form.get('registration_status', 'Buka'))
    set_config('registration_start', request.form.get('registration_start', '2026-07-01'))
    set_config('registration_end', request.form.get('registration_end', '2026-07-25'))
    set_config('max_sks', _safe_int(request.form.get('max_sks'), 9))
    flash("Pengaturan periode pendaftaran Semester Antara berhasil diperbarui.", "success")
    return redirect(url_for('prodi.periode'))


@prodi_bp.route('/katalog')
def katalog():
    courses = get_courses_list()
    lecturers = get_lecturers()
    return render_template(
        'prodi_katalog.html',
        courses=courses,
        lecturers=lecturers,
        active_tab='prodi_katalog',
    )


@prodi_bp.route('/katalog/add', methods=['POST'])
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
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('prodi.katalog'))


@prodi_bp.route('/katalog/edit/<int:course_id>', methods=['POST'])
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
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('prodi.katalog'))


@prodi_bp.route('/katalog/delete/<int:course_id>', methods=['POST'])
def katalog_delete(course_id: int):
    success, message = delete_course(course_id)
    flash(message, 'warning' if success else 'danger')
    return redirect(url_for('prodi.katalog'))


@prodi_bp.route('/jadwal_ruang')
def jadwal_ruang():
    courses = get_courses_list()
    return render_template('prodi_jadwal_ruang.html', courses=courses, active_tab='prodi_jadwal')


@prodi_bp.route('/jadwal/update/<int:course_id>', methods=['POST'])
def jadwal_update(course_id: int):
    day = request.form.get('schedule_day', 'Senin')
    time_str = request.form.get('schedule_time', '08.00 - 10.30 WIB')
    room = request.form.get('room', 'Ruang Kelas FST')

    update_course_schedule(course_id, day, time_str, room)
    flash("Jadwal dan alokasi ruang kuliah luring berhasil diperbarui.", "success")
    return redirect(url_for('prodi.jadwal_ruang'))


@prodi_bp.route('/monitoring')
def monitoring():
    courses = get_courses_list()
    return render_template('prodi_monitoring.html', courses=courses, active_tab='prodi_monitoring')


@prodi_bp.route('/status/<int:course_id>', methods=['POST'])
def set_class_status(course_id: int):
    new_status = request.form.get('status', 'Menunggu')
    update_course_status(course_id, new_status)
    flash(f"Status kelas #{course_id} berhasil ditetapkan menjadi: {new_status}.", "success")
    return redirect(url_for('prodi.monitoring'))


@prodi_bp.route('/rekap')
def rekap():
    participants = get_official_participants()
    return render_template('prodi_rekap.html', participants=participants, active_tab='prodi_rekap')


@prodi_bp.route('/tutup', methods=['POST'])
def tutup():
    set_config('registration_status', 'Tutup')
    flash(
        "Pendaftaran Semester Antara resmi DITUTUP. Akses pengisian KRS bagi mahasiswa telah dikunci.",
        "warning",
    )
    return redirect(url_for('prodi.rekap'))


@prodi_bp.route('/buka', methods=['POST'])
def buka():
    set_config('registration_status', 'Buka')
    flash("Pendaftaran Semester Antara telah DIBUKA kembali.", "success")
    return redirect(url_for('prodi.rekap'))


@prodi_bp.route('/export_csv')
def export_csv():
    participants = get_official_participants()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'NO', 'NIM', 'NAMA MAHASISWA', 'PROGRAM STUDI',
        'KODE MK', 'NAMA MATA KULIAH', 'SKS', 'RUANG KELAS',
        'HARI', 'WAKTU', 'DOSEN PENGAMPU', 'STATUS PEMBAYARAN', 'NO VIRTUAL ACCOUNT',
    ])

    for index, participant in enumerate(participants, 1):
        writer.writerow([
            index,
            participant['nim_nip'],
            participant['student_name'],
            participant['prodi'],
            participant['course_code'],
            participant['course_name'],
            participant['sks'],
            participant['room'],
            participant['schedule_day'],
            participant['schedule_time'],
            participant['lecturer_name'],
            participant['payment_status'],
            participant['va_number'] or '-',
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': 'attachment;filename=Rekapitulasi_Peserta_Semester_Antara_2026.csv'
        },
    )
