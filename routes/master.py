from flask import Blueprint, flash, redirect, render_template, request, url_for

from routes.decorators import roles_required
from services import (
    VALID_GRADES,
    create_program,
    create_user,
    delete_user,
    get_all_proposals,
    get_courses_list,
    get_dpas,
    get_lecturers,
    get_programs,
    get_student_grades,
    get_users_by_role,
    update_program,
    update_user,
    upsert_student_grade,
)

master_bp = Blueprint('master', __name__, url_prefix='/master')


def _safe_float(val, default: float = 3.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _safe_int(val, default: int = 1) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


# --- DATA MASTER MAHASISWA ---

@master_bp.route('/mahasiswa')
@roles_required('superadmin')
def mahasiswa_list():
    students = get_users_by_role('mahasiswa')
    dpas = get_dpas()
    programs = get_programs(active_only=False)
    courses = get_courses_list(prodi_code='ALL')

    grades_by_student = {s['id']: get_student_grades(s['id']) for s in students}
    return render_template(
        'master_mahasiswa.html',
        students=students,
        dpas=dpas,
        programs=programs,
        courses=courses,
        grades_by_student=grades_by_student,
        valid_grades=VALID_GRADES,
        active_tab='master_mahasiswa',
    )


@master_bp.route('/mahasiswa/add', methods=['POST'])
@roles_required('superadmin')
def mahasiswa_add():
    nim = (request.form.get('nim_nip') or '').strip()
    username = (request.form.get('username') or '').strip() or nim
    password = (request.form.get('password') or '').strip() or 'mhs123'
    name = request.form.get('name', '')
    prodi_code = (request.form.get('prodi_code') or '60').strip()
    prodi = request.form.get('prodi', 'Teknik Informatika')
    email = request.form.get('email', '')
    ipk = _safe_float(request.form.get('ipk'), 3.0)
    semester = _safe_int(request.form.get('semester'), 4)
    dpa_id = _safe_int(request.form.get('dpa_id'), 0) or None
    status_sanksi = request.form.get('status_sanksi', 'Aktif Bebas Sanksi')

    success, message = create_user(
        username=username,
        password=password,
        name=name,
        nim_nip=nim or username,
        role='mahasiswa',
        prodi=prodi,
        email=email,
        ipk=ipk,
        semester=semester,
        dpa_id=dpa_id,
        prodi_code=prodi_code,
        status_sanksi=status_sanksi,
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('master.mahasiswa_list'))


@master_bp.route('/mahasiswa/edit/<int:user_id>', methods=['POST'])
@roles_required('superadmin')
def mahasiswa_edit(user_id: int):
    dpa_id = _safe_int(request.form.get('dpa_id'), 0) or None
    prodi_code = (request.form.get('prodi_code') or '').strip() or None
    status_sanksi = request.form.get('status_sanksi', 'Aktif Bebas Sanksi')

    success, message = update_user(
        user_id=user_id,
        name=request.form.get('name', ''),
        nim_nip=request.form.get('nim_nip', ''),
        prodi=request.form.get('prodi', 'Teknik Informatika'),
        email=request.form.get('email', ''),
        ipk=_safe_float(request.form.get('ipk'), 3.0),
        semester=_safe_int(request.form.get('semester'), 4),
        new_password=request.form.get('new_password'),
        dpa_id=dpa_id,
        prodi_code=prodi_code,
        status_sanksi=status_sanksi,
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('master.mahasiswa_list'))


@master_bp.route('/mahasiswa/grade/<int:user_id>', methods=['POST'])
@roles_required('superadmin')
def mahasiswa_grade(user_id: int):
    success, message = upsert_student_grade(
        student_id=user_id,
        course_code=request.form.get('course_code', ''),
        grade=request.form.get('grade', 'C'),
        semester_taken=_safe_int(request.form.get('semester_taken'), 1),
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('master.mahasiswa_list'))


@master_bp.route('/mahasiswa/delete/<int:user_id>', methods=['POST'])
@roles_required('superadmin')
def mahasiswa_delete(user_id: int):
    success, message = delete_user(user_id)
    flash(message, 'warning' if success else 'danger')
    return redirect(url_for('master.mahasiswa_list'))


# --- DATA MASTER DOSEN (DPA, DOSEN PENGAMPU, ADMIN PRODI) ---

@master_bp.route('/dosen')
@roles_required('superadmin')
def dosen_list():
    lecturers = get_lecturers()
    programs = get_programs(active_only=False)
    return render_template(
        'master_dosen.html',
        lecturers=lecturers,
        programs=programs,
        active_tab='master_dosen',
    )


@master_bp.route('/dosen/add', methods=['POST'])
@roles_required('superadmin')
def dosen_add():
    role = request.form.get('role', 'dosen')
    if role not in ('dpa', 'dosen', 'prodi'):
        role = 'dosen'

    success, message = create_user(
        username=request.form.get('username', ''),
        password=request.form.get('password', '') or 'dosen123',
        name=request.form.get('name', ''),
        nim_nip=request.form.get('nim_nip', ''),
        role=role,
        prodi=request.form.get('prodi', 'Teknik Informatika'),
        email=request.form.get('email', ''),
        prodi_code=request.form.get('prodi_code', '60'),
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('master.dosen_list'))


@master_bp.route('/dosen/edit/<int:user_id>', methods=['POST'])
@roles_required('superadmin')
def dosen_edit(user_id: int):
    role = request.form.get('role')
    if role not in ('dpa', 'dosen', 'prodi'):
        role = None

    success, message = update_user(
        user_id=user_id,
        name=request.form.get('name', ''),
        nim_nip=request.form.get('nim_nip', ''),
        prodi=request.form.get('prodi', 'Teknik Informatika'),
        email=request.form.get('email', ''),
        role=role,
        new_password=request.form.get('new_password'),
        prodi_code=request.form.get('prodi_code'),
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('master.dosen_list'))


@master_bp.route('/dosen/delete/<int:user_id>', methods=['POST'])
@roles_required('superadmin')
def dosen_delete(user_id: int):
    success, message = delete_user(user_id)
    flash(message, 'warning' if success else 'danger')
    return redirect(url_for('master.dosen_list'))


# --- DATA MASTER PROGRAM STUDI ---

@master_bp.route('/prodi')
@roles_required('superadmin')
def prodi_list():
    programs = get_programs(active_only=False)
    return render_template('master_prodi.html', programs=programs, active_tab='master_prodi')


@master_bp.route('/prodi/add', methods=['POST'])
@roles_required('superadmin')
def prodi_add():
    success, message = create_program(
        code=request.form.get('code', ''),
        name=request.form.get('name', ''),
        faculty=request.form.get('faculty', 'Fakultas Sains dan Teknologi'),
        rumpun_ilmu=request.form.get('rumpun_ilmu', 'Sarjana Reguler'),
        status_buka_sa=request.form.get('status_buka_sa', 'Menyelenggarakan'),
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('master.prodi_list'))


@master_bp.route('/prodi/edit/<code>', methods=['POST'])
@roles_required('superadmin')
def prodi_edit(code: str):
    success, message = update_program(
        code=code,
        name=request.form.get('name', ''),
        faculty=request.form.get('faculty', ''),
        rumpun_ilmu=request.form.get('rumpun_ilmu', 'Sarjana Reguler'),
        status_buka_sa=request.form.get('status_buka_sa', 'Menyelenggarakan'),
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('master.prodi_list'))
