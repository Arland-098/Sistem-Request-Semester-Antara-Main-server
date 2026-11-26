from flask import Blueprint, flash, redirect, render_template, request, url_for

from routes.decorators import get_logged_in_user, normalize_role, roles_required
from services import (
    confirm_lecturer_dispensation,
    confirm_lecturer_teaching,
    get_course_by_id,
    get_courses_list,
    get_lecturer_related_applications,
    lecturer_review_application,
)

dosen_bp = Blueprint('dosen', __name__)


def _resolve_lecturer_scope():
    user = get_logged_in_user()
    if user and normalize_role(user['role']) == 'superadmin':
        return None, True
    return user['id'], False


@dosen_bp.route('/dosen')
@roles_required('dosen')
def dashboard():
    lecturer_id, allow_any = _resolve_lecturer_scope()
    courses = get_courses_list()
    my_courses = courses if allow_any else [c for c in courses if c['lecturer_id'] == lecturer_id]
    related_apps = get_lecturer_related_applications(None if allow_any else lecturer_id)
    return render_template(
        'dosen_dashboard.html',
        courses=my_courses,
        related_apps=related_apps,
        active_tab='dosen',
    )


@dosen_bp.route('/dosen/confirm/<int:course_id>', methods=['POST'])
@roles_required('dosen')
def confirm(course_id: int):
    lecturer_id, allow_any = _resolve_lecturer_scope()
    course = get_course_by_id(course_id)
    if not course or (not allow_any and course['lecturer_id'] != lecturer_id):
        flash("Anda tidak berwenang mengonfirmasi mata kuliah tersebut.", "danger")
        return redirect(url_for('dosen.dashboard'))

    agreed = request.form.get('agreed') == '1'
    confirm_lecturer_teaching(course_id, agreed)
    status_str = "BERSEDIA MENGAJAR" if agreed else "MENOLAK MENGAJAR"
    flash(f"Konfirmasi mengajar berhasil disimpan: {status_str}.", "success")
    return redirect(url_for('dosen.dashboard'))


@dosen_bp.route('/dosen/dispensasi/<int:course_id>', methods=['POST'])
@roles_required('dosen')
def dispensasi(course_id: int):
    lecturer_id, allow_any = _resolve_lecturer_scope()
    course = get_course_by_id(course_id)
    if not course or (not allow_any and course['lecturer_id'] != lecturer_id):
        flash("Anda tidak berwenang mengonfirmasi kelas dispensasi untuk mata kuliah tersebut.", "danger")
        return redirect(url_for('dosen.dashboard'))

    agreed = request.form.get('agreed') == '1'
    confirm_lecturer_dispensation(course_id, agreed)
    status_str = "BERSEDIA MENGAJAR KELAS DISPENSASI" if agreed else "MENOLAK KELAS DISPENSASI"
    flash(f"Konfirmasi kelas dispensasi berhasil disimpan: {status_str}.", "info")
    return redirect(url_for('dosen.dashboard'))


@dosen_bp.route('/dosen/review/<int:app_id>', methods=['POST'])
@roles_required('dosen')
def review_application(app_id: int):
    lecturer_id, allow_any = _resolve_lecturer_scope()
    decision = request.form.get('decision', 'approve')
    notes = request.form.get('notes', '')

    success, message = lecturer_review_application(
        app_id,
        lecturer_id,
        decision,
        notes,
        allow_any=allow_any,
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('dosen.dashboard'))
