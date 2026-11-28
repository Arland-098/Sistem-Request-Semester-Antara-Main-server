from flask import Blueprint, flash, redirect, render_template, request, url_for

from routes.decorators import ROLE_LABELS, get_logged_in_user, roles_required
from services import VALID_ROLES, create_user, delete_user, get_all_users, get_dpas, get_programs, update_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users')
@roles_required('superadmin')
def users_list():
    users = get_all_users()
    dpas = get_dpas()
    programs = get_programs(active_only=False)
    return render_template(
        'admin_users.html',
        users=users,
        dpas=dpas,
        programs=programs,
        valid_roles=VALID_ROLES,
        role_labels=ROLE_LABELS,
        active_tab='admin_users',
    )


@admin_bp.route('/users/add', methods=['POST'])
@roles_required('superadmin')
def users_add():
    role = request.form.get('role', 'mahasiswa')
    try:
        ipk = float(request.form.get('ipk') or 0.0)
    except (TypeError, ValueError):
        ipk = 0.0
    try:
        semester = int(request.form.get('semester') or 0)
    except (TypeError, ValueError):
        semester = 0
    try:
        dpa_id = int(request.form.get('dpa_id') or 0) or None
    except (TypeError, ValueError):
        dpa_id = None

    success, message = create_user(
        username=request.form.get('username', ''),
        password=request.form.get('password', ''),
        name=request.form.get('name', ''),
        nim_nip=request.form.get('nim_nip', ''),
        role=role,
        prodi=request.form.get('prodi', 'Teknik Informatika'),
        email=request.form.get('email', ''),
        ipk=ipk,
        semester=semester,
        dpa_id=dpa_id,
        prodi_code=request.form.get('prodi_code', '60'),
        status_sanksi=request.form.get('status_sanksi', 'Aktif Bebas Sanksi'),
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/edit/<int:user_id>', methods=['POST'])
@roles_required('superadmin')
def users_edit(user_id: int):
    current = get_logged_in_user()
    is_active = 1 if request.form.get('is_active') == '1' else 0
    if current and current['id'] == user_id and is_active == 0:
        flash("Anda tidak dapat menonaktifkan akun Super Admin yang sedang login.", "danger")
        return redirect(url_for('admin.users_list'))

    role = request.form.get('role')
    if current and current['id'] == user_id and role != 'superadmin':
        flash("Anda tidak dapat menurunkan peran akun Anda sendiri saat sedang login.", "danger")
        return redirect(url_for('admin.users_list'))

    success, message = update_user(
        user_id=user_id,
        name=request.form.get('name', ''),
        nim_nip=request.form.get('nim_nip', ''),
        prodi=request.form.get('prodi', 'Teknik Informatika'),
        email=request.form.get('email', ''),
        role=role,
        new_password=request.form.get('new_password'),
        is_active=is_active,
        status_sanksi=request.form.get('status_sanksi'),
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@roles_required('superadmin')
def users_delete(user_id: int):
    current = get_logged_in_user()
    if current and current['id'] == user_id:
        flash("Tidak dapat menghapus akun yang sedang login.", "danger")
        return redirect(url_for('admin.users_list'))

    success, message = delete_user(user_id)
    flash(message, 'warning' if success else 'danger')
    return redirect(url_for('admin.users_list'))
