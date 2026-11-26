from flask import Blueprint, flash, redirect, render_template, request, url_for

from routes.decorators import get_logged_in_user, normalize_role, roles_required
from services import (
    get_courses_grouped_by_semester,
    get_courses_list,
    get_student_application,
    get_user_by_id,
    get_user_by_username,
    submit_student_krs,
)

mahasiswa_bp = Blueprint('mahasiswa', __name__)


def _resolve_student_id() -> int:
    user = get_logged_in_user()
    if user and normalize_role(user['role']) == 'mahasiswa':
        return user['id']
    default_student = get_user_by_username('1251420125')
    return default_student['id'] if default_student else 1


@mahasiswa_bp.route('/katalog')
@roles_required('mahasiswa')
def katalog():
    courses = get_courses_list()
    grouped_courses = get_courses_grouped_by_semester()
    selected_prodi = request.args.get('prodi', '60')
    return render_template(
        'mahasiswa_katalog.html',
        courses=courses,
        grouped_courses=grouped_courses,
        selected_prodi=selected_prodi,
        active_tab='katalog',
    )


@mahasiswa_bp.route('/krs')
@roles_required('mahasiswa')
def krs():
    student_id = _resolve_student_id()
    student = get_user_by_id(student_id)
    app_data, krs_items, invoice = get_student_application(student_id)
    courses = get_courses_list()
    grouped_courses = get_courses_grouped_by_semester()
    current_selected_ids = [item['course_id'] for item in krs_items] if krs_items else []

    return render_template(
        'mahasiswa_krs.html',
        student=student,
        app=app_data,
        krs_items=krs_items,
        invoice=invoice,
        available_courses=courses,
        grouped_courses=grouped_courses,
        current_selected_ids=current_selected_ids,
        active_tab='krs',
    )


@mahasiswa_bp.route('/krs/submit', methods=['POST'])
@roles_required('mahasiswa')
def krs_submit():
    student_id = _resolve_student_id()
    course_ids = request.form.getlist('course_ids', type=int)

    success, message = submit_student_krs(student_id, course_ids)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('mahasiswa.krs'))


@mahasiswa_bp.route('/tagihan')
@roles_required('mahasiswa')
def tagihan():
    student_id = _resolve_student_id()
    student = get_user_by_id(student_id)
    app_data, krs_items, invoice = get_student_application(student_id)

    return render_template(
        'mahasiswa_tagihan.html',
        student=student,
        app=app_data,
        invoice=invoice,
        items=krs_items,
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

    return render_template(
        'mahasiswa_cetak_krs.html',
        student=student,
        app=app_data,
        items=krs_items,
        invoice=invoice,
    )
