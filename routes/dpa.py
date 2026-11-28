from flask import Blueprint, flash, redirect, render_template, request, url_for

from routes.decorators import get_logged_in_user, normalize_role, roles_required
from services import approve_student_krs, get_dpa_applications, reject_student_krs

dpa_bp = Blueprint('dpa', __name__)


def _resolve_dpa_scope():
    user = get_logged_in_user()
    if user and normalize_role(user['role']) == 'superadmin':
        return None, True
    return (user['id'] if user else None), False


@dpa_bp.route('/dpa')
@roles_required('dpa')
def dashboard():
    dpa_id, allow_any = _resolve_dpa_scope()
    applications = get_dpa_applications(dpa_id=None if allow_any else dpa_id)
    return render_template('dpa_dashboard.html', applications=applications, active_tab='dpa')


@dpa_bp.route('/dpa/approve/<int:app_id>', methods=['POST'])
@roles_required('dpa')
def approve(app_id: int):
    dpa_id, allow_any = _resolve_dpa_scope()
    notes = (request.form.get('notes') or '').strip()
    success, message = approve_student_krs(
        app_id,
        dpa_id=dpa_id,
        notes=notes,
        allow_any=allow_any,
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('dpa.dashboard'))


@dpa_bp.route('/dpa/reject/<int:app_id>', methods=['POST'])
@roles_required('dpa')
def reject(app_id: int):
    dpa_id, allow_any = _resolve_dpa_scope()
    notes = (request.form.get('notes') or '').strip() or 'Silakan konsultasi dan perbaiki pilihan mata kuliah.'
    success, message = reject_student_krs(
        app_id,
        notes=notes,
        dpa_id=dpa_id,
        allow_any=allow_any,
    )
    flash(message, 'warning' if success else 'danger')
    return redirect(url_for('dpa.dashboard'))
