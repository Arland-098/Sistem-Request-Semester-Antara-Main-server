from flask import Blueprint, flash, redirect, render_template, request, url_for

from routes.decorators import roles_required
from services import (
    create_user,
    delete_user,
    get_lecturers,
    get_users_by_role,
    update_user,
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
@roles_required('admin_akademik')
def mahasiswa_list():
    students = get_users_by_role('mahasiswa')
    return render_template(
        'master_mahasiswa.html',
        students=students,
        active_tab='master_mahasiswa',
    )


@master_bp.route('/mahasiswa/add', methods=['POST'])
@roles_required('admin_akademik')
def mahasiswa_add():
    nim = (request.form.get('nim_nip') or '').strip()
    username = (request.form.get('username') or '').strip() or nim
    password = (request.form.get('password') or '').strip() or 'mhs123'
    name = request.form.get('name', '')
    prodi = request.form.get('prodi', 'Teknik Informatika')
    email = request.form.get('email', '')
    ipk = _safe_float(request.form.get('ipk'), 3.0)
    semester = _safe_int(request.form.get('semester'), 4)

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
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('master.mahasiswa_list'))


@master_bp.route('/mahasiswa/edit/<int:user_id>', methods=['POST'])
@roles_required('admin_akademik')
def mahasiswa_edit(user_id: int):
    success, message = update_user(
        user_id=user_id,
        name=request.form.get('name', ''),
        nim_nip=request.form.get('nim_nip', ''),
        prodi=request.form.get('prodi', 'Teknik Informatika'),
        email=request.form.get('email', ''),
        ipk=_safe_float(request.form.get('ipk'), 3.0),
        semester=_safe_int(request.form.get('semester'), 4),
        new_password=request.form.get('new_password'),
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('master.mahasiswa_list'))


@master_bp.route('/mahasiswa/delete/<int:user_id>', methods=['POST'])
@roles_required('admin_akademik')
def mahasiswa_delete(user_id: int):
    success, message = delete_user(user_id)
    flash(message, 'warning' if success else 'danger')
    return redirect(url_for('master.mahasiswa_list'))


# --- DATA MASTER DOSEN ---

@master_bp.route('/dosen')
@roles_required('admin_akademik')
def dosen_list():
    lecturers = get_lecturers()
    return render_template(
        'master_dosen.html',
        lecturers=lecturers,
        active_tab='master_dosen',
    )


@master_bp.route('/dosen/add', methods=['POST'])
@roles_required('admin_akademik')
def dosen_add():
    role = request.form.get('role', 'dosen')
    if role not in ('dosen', 'kaprodi'):
        role = 'dosen'

    success, message = create_user(
        username=request.form.get('username', ''),
        password=request.form.get('password', '') or 'dosen123',
        name=request.form.get('name', ''),
        nim_nip=request.form.get('nim_nip', ''),
        role=role,
        prodi=request.form.get('prodi', 'Teknik Informatika'),
        email=request.form.get('email', ''),
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('master.dosen_list'))


@master_bp.route('/dosen/edit/<int:user_id>', methods=['POST'])
@roles_required('admin_akademik')
def dosen_edit(user_id: int):
    role = request.form.get('role')
    if role not in ('dosen', 'kaprodi'):
        role = None

    success, message = update_user(
        user_id=user_id,
        name=request.form.get('name', ''),
        nim_nip=request.form.get('nim_nip', ''),
        prodi=request.form.get('prodi', 'Teknik Informatika'),
        email=request.form.get('email', ''),
        role=role,
        new_password=request.form.get('new_password'),
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('master.dosen_list'))


@master_bp.route('/dosen/delete/<int:user_id>', methods=['POST'])
@roles_required('admin_akademik')
def dosen_delete(user_id: int):
    success, message = delete_user(user_id)
    flash(message, 'warning' if success else 'danger')
    return redirect(url_for('master.dosen_list'))
