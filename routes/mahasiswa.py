from flask import Blueprint, flash, redirect, render_template, request, url_for

from routes.decorators import get_logged_in_user, normalize_role, roles_required
from services import (
    PARTNER_BANKS,
    cancel_student_krs,
    get_announcements,
    get_config,
    get_courses_grouped_by_semester,
    get_courses_list,
    get_equivalences,
    get_programs,
    get_student_application,
    get_student_grades,
    get_student_grades_map,
    get_student_proposals,
    get_user_by_id,
    get_user_by_username,
    submit_course_proposal,
    submit_student_krs,
)

mahasiswa_bp = Blueprint('mahasiswa', __name__)


def _resolve_student_id() -> int:
    user = get_logged_in_user()
    if user and normalize_role(user['role']) == 'mahasiswa':
        return user['id']
    default_student = get_user_by_username('1084729301')
    return default_student['id'] if default_student else 1


@mahasiswa_bp.route('/katalog')
@roles_required('mahasiswa')
def katalog():
    selected_prodi = request.args.get('prodi', '60')
    courses = get_courses_list(prodi_code=selected_prodi)
    grouped_courses = get_courses_grouped_by_semester(prodi_code=selected_prodi)
    programs = get_programs(active_only=True)
    announcements = get_announcements(active_only=True)
    return render_template(
        'mahasiswa_katalog.html',
        courses=courses,
        grouped_courses=grouped_courses,
        programs=programs,
        announcements=announcements,
        selected_prodi=selected_prodi,
        active_tab='katalog',
    )


@mahasiswa_bp.route('/usulan', methods=['GET', 'POST'])
@roles_required('mahasiswa')
def usulan():
    student_id = _resolve_student_id()
    student = get_user_by_id(student_id)
    programs = get_programs(active_only=True)

    if request.method == 'POST':
        is_cross_prodi = request.form.get('is_cross_prodi') == '1'
        target_prodi_code = (
            request.form.get('target_prodi_code', '55')
            if is_cross_prodi
            else (student['prodi_code'] or '60')
        )
        try:
            sks = int(request.form.get('sks', '3'))
        except (TypeError, ValueError):
            sks = 3
        try:
            semester_target = int(request.form.get('semester_target', '1'))
        except (TypeError, ValueError):
            semester_target = 1

        success, message = submit_course_proposal(
            student_id=student_id,
            target_prodi_code=target_prodi_code,
            course_code=request.form.get('course_code', ''),
            course_name=request.form.get('course_name', ''),
            sks=sks,
            semester_target=semester_target,
            is_cross_prodi=is_cross_prodi,
            origin_course_code=request.form.get('origin_course_code', ''),
            origin_course_name=request.form.get('origin_course_name', ''),
            syllabus_summary=request.form.get('syllabus_summary', ''),
            reason=request.form.get('reason', ''),
        )
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('mahasiswa.usulan'))

    proposals = get_student_proposals(student_id)
    equivalences = get_equivalences()
    return render_template(
        'mahasiswa_usulan.html',
        student=student,
        programs=programs,
        proposals=proposals,
        equivalences=equivalences,
        active_tab='usulan',
    )


@mahasiswa_bp.route('/krs')
@roles_required('mahasiswa')
def krs():
    student_id = _resolve_student_id()
    student = get_user_by_id(student_id)
    app_data, krs_items, invoice = get_student_application(student_id)
    courses = get_courses_list(prodi_code='ALL')
    grouped_courses = get_courses_grouped_by_semester(prodi_code='ALL')
    grades_map = get_student_grades_map(student_id)
    student_grades = get_student_grades(student_id)

    active_items = [item for item in krs_items if item['status'] == 'Aktif'] if krs_items else []
    current_selected_ids = [item['course_id'] for item in active_items]
    current_jenis_map = {item['course_id']: item['jenis_pengambilan'] for item in active_items}

    return render_template(
        'mahasiswa_krs.html',
        student=student,
        app=app_data,
        krs_items=krs_items,
        invoice=invoice,
        available_courses=courses,
        grouped_courses=grouped_courses,
        grades_map=grades_map,
        student_grades=student_grades,
        current_selected_ids=current_selected_ids,
        current_jenis_map=current_jenis_map,
        partner_banks=PARTNER_BANKS,
        active_tab='krs',
    )


@mahasiswa_bp.route('/krs/submit', methods=['POST'])
@roles_required('mahasiswa')
def krs_submit():
    student_id = _resolve_student_id()
    course_ids = request.form.getlist('course_ids', type=int)
    preferred_bank = request.form.get('preferred_bank', 'Bank Mandiri')

    selections = []
    for cid in course_ids:
        jenis = request.form.get(f'jenis_{cid}')
        selections.append({'course_id': cid, 'jenis_pengambilan': jenis})

    success, message = submit_student_krs(student_id, selections, preferred_bank=preferred_bank)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('mahasiswa.krs'))


@mahasiswa_bp.route('/krs/cancel', methods=['POST'])
@roles_required('mahasiswa')
def krs_cancel():
    student_id = _resolve_student_id()
    success, message = cancel_student_krs(student_id)
    flash(message, 'info' if success else 'danger')
    return redirect(url_for('mahasiswa.krs'))


@mahasiswa_bp.route('/tagihan')
@roles_required('mahasiswa')
def tagihan():
    student_id = _resolve_student_id()
    student = get_user_by_id(student_id)
    app_data, krs_items, invoice = get_student_application(student_id)
    rumpun = (student['rumpun_ilmu'] if student else 'Sarjana Reguler') or 'Sarjana Reguler'
    if rumpun == 'Ilmu Kesehatan':
        student_rate = int(get_config('sks_rate_kesehatan', '850000') or 850000)
    else:
        student_rate = int(get_config('sks_rate', '220000') or 220000)

    return render_template(
        'mahasiswa_tagihan.html',
        student=student,
        app=app_data,
        invoice=invoice,
        items=krs_items,
        student_rate=student_rate,
        student_rumpun=rumpun,
        active_tab='tagihan',
    )


@mahasiswa_bp.route('/cetak_krs')
@roles_required('mahasiswa')
def cetak_krs():
    student_id = _resolve_student_id()
    student = get_user_by_id(student_id)
    app_data, krs_items, invoice = get_student_application(student_id)

    if not app_data or app_data['status'] != 'Lunas':
        flash(
            "Pencetakan Kartu Rencana Studi Sah hanya dapat dilakukan setelah status pembayaran lunas.",
            "warning",
        )
        return redirect(url_for('mahasiswa.tagihan'))

    active_items = [item for item in krs_items if item['status'] == 'Aktif']
    return render_template(
        'mahasiswa_cetak_krs.html',
        student=student,
        app=app_data,
        items=active_items,
        invoice=invoice,
    )
