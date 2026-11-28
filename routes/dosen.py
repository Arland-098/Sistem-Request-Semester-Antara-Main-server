from flask import Blueprint, flash, redirect, render_template, request, url_for

from routes.decorators import get_logged_in_user, normalize_role, roles_required
from services import (
    confirm_lecturer_dispensation,
    confirm_lecturer_teaching,
    get_course_by_id,
    get_courses_list,
    get_lecturer_official_roster,
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
    courses = get_courses_list(prodi_code='ALL')
    my_courses = courses if allow_any else [c for c in courses if c['lecturer_id'] == lecturer_id]
    dispensation_courses = [
        c for c in my_courses
        if c['dispensation_requested'] == 1 or c['status'] == 'Menunggu Kebijakan Prodi'
    ]
    official_roster = get_lecturer_official_roster(None if allow_any else lecturer_id)

    return render_template(
        'dosen_dashboard.html',
        courses=my_courses,
        dispensation_courses=dispensation_courses,
        official_roster=official_roster,
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
    status_str = "BERSEDIA MENGAJAR KELAS DISPENSASI" if agreed else "TIDAK BERSEDIA MENGAJAR KELAS DISPENSASI"
    flash(
        f"Konfirmasi kelas dispensasi berhasil dikirim ke Program Studi: {status_str} (SD-03).",
        "info",
    )
    return redirect(url_for('dosen.dashboard'))
