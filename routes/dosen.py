from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services import (
    confirm_lecturer_dispensation,
    confirm_lecturer_teaching,
    get_courses_list,
    get_user_by_id,
    get_user_by_username,
)

dosen_bp = Blueprint('dosen', __name__)


def _resolve_lecturer_id() -> int:
    user_id = session.get('user_id')
    if user_id:
        user = get_user_by_id(user_id)
        if user and user['role'] in ('dosen', 'dpa'):
            return user['id']
    default_dosen = get_user_by_username('dosen1')
    return default_dosen['id'] if default_dosen else 6


@dosen_bp.route('/dosen')
def dashboard():
    lecturer_id = _resolve_lecturer_id()
    courses = get_courses_list()
    my_courses = [c for c in courses if c['lecturer_id'] == lecturer_id]
    return render_template('dosen_dashboard.html', courses=my_courses, active_tab='dosen')


@dosen_bp.route('/dosen/confirm/<int:course_id>', methods=['POST'])
def confirm(course_id: int):
    agreed = request.form.get('agreed') == '1'
    confirm_lecturer_teaching(course_id, agreed)
    status_str = "BERSEDIA MENGAJAR" if agreed else "MENOLAK MENGAJAR"
    flash(f"Konfirmasi mengajar berhasil disimpan: {status_str}.", "success")
    return redirect(url_for('dosen.dashboard'))


@dosen_bp.route('/dosen/dispensasi/<int:course_id>', methods=['POST'])
def dispensasi(course_id: int):
    agreed = request.form.get('agreed') == '1'
    confirm_lecturer_dispensation(course_id, agreed)
    status_str = "BERSEDIA MENGAJAR KELAS DISPENSASI" if agreed else "MENOLAK KELAS DISPENSASI"
    flash(f"Konfirmasi kelas dispensasi berhasil disimpan: {status_str}.", "info")
    return redirect(url_for('dosen.dashboard'))
